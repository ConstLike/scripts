#include <atomic>
#include <iostream>
#include <fstream>
#include <sstream>
#include <vector>
#include <string>
#include <filesystem>
#include <algorithm>
#include <map>
#include <optional>
#include <stdexcept>

namespace fs = std::__fs::filesystem;

/**
 * @brief Configuration settings for OpenQPInputGenerator
 *
 * This struct encapsulates all the configuration parameters needed
 * for initializing an OpenQPInputGenerator object.
 */
struct OpenQPInputGeneratorConfig {
    std::vector<std::string> methods;
    std::vector<std::string> basis_sets;
    std::vector<std::string> functionals;
    std::vector<std::string> scf_types;
    std::vector<std::string> tddft_types;
    std::string xyz_file;
    bool include_hf{true};
};

/**
 * @brief Generator for OpenQP input configurations
 *
 * This class is responsible for generating input configurations
 * for OpenQP based on the provided settings.
 */
class OpenQPInputGenerator {
public:
    /**
     * @brief Construct a new OpenQPInputGenerator object
     *
     * @param config Configuration settings for the generator
     * @throws std::runtime_error if the XYZ file is not found
     */
    explicit OpenQPInputGenerator(const OpenQPInputGeneratorConfig& config)
        : config_(config),
          system_geometry_(read_xyz_file(config.xyz_file)),
          name_xyz_(extract_xyz_name(config.xyz_file)) {}

    /**
     * @brief Generate input configurations based on the current settings
     *
     * @return std::vector<std::map<std::string, std::string>> Vector of input configurations
     */
    std::vector<std::map<std::string, std::string>> generate_input_configurations() {
        std::vector<std::map<std::string, std::string>> input_configurations;

        for (const auto& method : config_.methods) {
            for (const auto& basis : config_.basis_sets) {
                for (const auto& functional : config_.functionals) {
                    for (const auto& scf_type : config_.scf_types) {
                        int scf_mult = (scf_type == "rhf" || scf_type == "uhf-s") ? 1 : 3;
                        std::string scf = scf_type.substr(0, scf_type.find('-'));
                        if (method == "hf" && config_.include_hf) {
                            auto config = build_configuration(scf, scf_mult, method, basis, functional, "",
                                                              name_xyz_ + "_" + scf_type + "_" + basis + "_" + functional + ".inp");
                            input_configurations.push_back(config);
                        } else if (method == "tdhf") {
                            for (const auto& tddft : config_.tddft_types) {
                                if (is_valid_tddft_scf_combination(scf, tddft)) {
                                    std::string file_name = name_xyz_ + "_" + scf_type + "_" + tddft + "_" + basis + "_" + functional + ".inp";
                                    auto config = build_configuration(scf, scf_mult, method, basis, functional, tddft, file_name);
                                    input_configurations.push_back(config);
                                }
                            }
                        }
                    }
                }
            }
        }

        return input_configurations;
    }

    /**
     * @brief Get a string representation of the generator
     *
     * @return std::string Description of the generator's configuration
     */
    std::string to_string() const {
        return "OpenQPInputGenerator with " + std::to_string(config_.methods.size()) + " methods, " +
               std::to_string(config_.basis_sets.size()) + " basis sets, " +
               std::to_string(config_.functionals.size()) + " functionals, " +
               std::to_string(config_.scf_types.size()) + " SCF types, and " +
               std::to_string(config_.tddft_types.size()) + " TDDFT types.";
    }

private:
    OpenQPInputGeneratorConfig config_;
    std::string system_geometry_;
    std::string name_xyz_;

    static const std::map<std::string, int> atom_numbers_;

    /**
     * @brief Read and process an XYZ file
     *
     * @param xyz_file Path to the XYZ file
     * @return std::string Processed geometry string
     * @throws std::runtime_error if the file is not found or cannot be read
     */
    static std::string read_xyz_file(const std::string& xyz_file) {
        if (!fs::exists(xyz_file)) {
            throw std::runtime_error("XYZ file not found: " + xyz_file);
        }

        std::ifstream file(xyz_file);
        if (!file.is_open()) {
            throw std::runtime_error("Unable to open XYZ file: " + xyz_file);
        }

        std::string line;
        std::getline(file, line); // Skip first line
        std::getline(file, line); // Skip second line

        std::ostringstream geometry;
        while (std::getline(file, line)) {
            std::istringstream iss(line);
            std::string atom;
            double x, y, z;
            if (iss >> atom >> x >> y >> z) {
                if (std::all_of(atom.begin(), atom.end(), ::isdigit)) {
                    int atom_number = std::stoi(atom);
                    auto it = std::find_if(atom_numbers_.begin(), atom_numbers_.end(),
                        [atom_number](const auto& pair) { return pair.second == atom_number; });
                    if (it != atom_numbers_.end()) {
                        atom = it->first;
                    }
                } else {
                    atom[0] = std::toupper(atom[0]);
                    std::transform(atom.begin() + 1, atom.end(), atom.begin() + 1, ::tolower);
                }
                geometry << " " << atom << " " << std::fixed << std::setprecision(9)
                         << x << " " << y << " " << z << "\n";
            }
        }
        return geometry.str();
    }

    /**
     * @brief Extract the name from an XYZ file path
     *
     * @param xyz_file Path to the XYZ file
     * @return std::string Extracted name
     */
    static std::string extract_xyz_name(const std::string& xyz_file) {
        return fs::path(xyz_file).stem().string();
    }

    /**
     * @brief Check if a TDDFT and SCF combination is valid
     *
     * @param scf SCF type
     * @param tddft TDDFT type
     * @return true if the combination is valid, false otherwise
     */
    static bool is_valid_tddft_scf_combination(const std::string& scf, const std::string& tddft) {
        if (scf == "rhf") {
            return tddft == "rpa-s" || tddft == "rpa-t" || tddft == "tda-s" || tddft == "tda-t";
        } else if (scf == "rohf") {
            return tddft == "mrsf-s" || tddft == "mrsf-t" || tddft == "mrsf-q" || tddft == "sf";
        }
        return false;
    }

    /**
     * @brief Determine the TDDFT multiplicity
     *
     * @param tddft TDDFT type
     * @return int Multiplicity
     */
    static int determine_tddft_multiplicity(const std::string& tddft) {
        if (tddft.empty()) return 0;
        if (tddft.find("-s") != std::string::npos) return 1;
        if (tddft.find("-t") != std::string::npos) return 3;
        if (tddft.find("-q") != std::string::npos) return 5;
        return 1;
    }

    /**
     * @brief Build a configuration based on the provided parameters
     *
     * @param scf SCF type
     * @param scf_mult SCF multiplicity
     * @param method Method
     * @param basis Basis set
     * @param functional Functional
     * @param tddft TDDFT type
     * @param file_name Output file name
     * @return std::map<std::string, std::string> Configuration map
     */
    std::map<std::string, std::string> build_configuration(const std::string& scf, int scf_mult,
                                                           const std::string& method, const std::string& basis,
                                                           const std::string& functional, const std::string& tddft,
                                                           const std::string& file_name) const {
        int tddft_mult = determine_tddft_multiplicity(tddft);

        std::map<std::string, std::string> config;
        config["file_name"] = file_name;

        // Input section
        config["input"] = "[input]\n"
                          "system=\n " + system_geometry_ +
                          "charge=0\n"
                          "method=" + method + "\n"
                          "basis=" + basis + "\n"
                          "runtype=grad\n"
                          "functional=" + functional + "\n"
                          "d4=false\n";

        // Guess section
        config["guess"] = "[guess]\n"
                          "type=huckel\n"
                          "save_mol=true\n";

        // SCF section
        config["scf"] = "[scf]\n"
                        "type=" + scf + "\n"
                        "maxit=100\n"
                        "maxdiis=5\n"
                        "multiplicity=" + std::to_string(scf_mult) + "\n"
                        "conv=1.0e-7\n"
                        "save_molden=true\n";

        // DFT grid section
        config["dftgrid"] = "[dftgrid]\n"
                            "rad_npts=96\n"
                            "ang_npts=302\n"
                            "pruned=\n";

        // Properties section
        config["properties"] = "[properties]\n"
                               "grad=" + std::to_string(tddft.empty() ? 0 : 3) + "\n";

        // TDHF section (if applicable)
        if (!tddft.empty()) {
            config["tdhf"] = "[tdhf]\n"
                             "type=" + tddft.substr(0, tddft.find('-')) + "\n"
                             "maxit=30\n"
                             "multiplicity=" + std::to_string(tddft_mult) + "\n"
                             "conv=1.0e-10\n"
                             "nstate=10\n"
                             "zvconv=1.0e-10\n";
        }

        return config;
    }
};

// Static member initialization
const std::map<std::string, int> OpenQPInputGenerator::atom_numbers_ = {
    {"H", 1}, {"He", 2}, {"Li", 3}, {"Be", 4}, {"B", 5}, {"C", 6}, {"N", 7}, {"O", 8}, {"F", 9}, {"Ne", 10},
    // ... (остальные элементы)
};

/**
 * @brief Process a directory containing XYZ files
 *
 * @param xyz_dir Directory containing XYZ files
 * @throws std::runtime_error if the directory is invalid or empty
 */
void process_directory(const std::string& xyz_dir) {
    if (!fs::is_directory(xyz_dir)) {
        throw std::runtime_error("Error: " + xyz_dir + " is not a valid directory.");
    }

    std::vector<fs::path> xyz_files;
    for (const auto& entry : fs::directory_iterator(xyz_dir)) {
        if (entry.path().extension() == ".xyz") {
            xyz_files.push_back(entry.path());
        }
    }

    if (xyz_files.empty()) {
        throw std::runtime_error("Error: No XYZ files found in " + xyz_dir + ".");
    }

    for (const auto& xyz_file : xyz_files) {
        std::string project_name = xyz_file.stem().string();
        std::cout << "Processing " << xyz_file << "..." << std::endl;

        OpenQPInputGeneratorConfig config{
            .methods = {"tdhf"},
            .basis_sets = {"cc-pVDZ"},
            .functionals = {"slater", "bhhlyp", "dtcam-aee"},
            .scf_types = {"rohf"},
            .tddft_types = {"mrsf-s"},
            .xyz_file = xyz_file.string(),
            .include_hf = false
        };

        OpenQPInputGenerator generator(config);

        auto inputs = generator.generate_input_configurations();

        std::string output_dir = xyz_dir;
        fs::create_directories(output_dir);

        for (const auto& config : inputs) {
            std::string file_path = (fs::path(output_dir) / config.at("file_name")).string();
            std::ofstream file(file_path);
            if (file.is_open()) {
                for (const auto& [section, content] : config) {
                    if (section != "file_name") {
                        file << content << "\n";
                    }
                }
                file.close();
            } else {
                std::cerr << "Unable to open file: " << file_path << std::endl;
            }
        }

         // Print inputs
        for (const auto& config : inputs) {
            std::cout << "File Name: " << config.at("file_name") << std::endl;
            std::cout << "Method: " << config.at("input").substr(config.at("input").find("method=") + 7,
                                                                 config.at("input").find('\n', config.at("input").find("method=")) -
                                                                 (config.at("input").find("method=") + 7))
                      << std::endl;
            if (config.find("tdhf") != config.end()) {
                std::cout << "TDHF Section:" << std::endl;
                std::istringstream tdhf_stream(config.at("tdhf"));
                std::string line;
                while (std::getline(tdhf_stream, line)) {
                    if (!line.empty() && line != "[tdhf]") {
                        std::cout << "  " << line << std::endl;
                    }
                }
            }
            std::cout << std::string(30, '-') << std::endl;
        }
    }
}

/**
 * @brief Main function
 *
 * @param argc Argument count
 * @param argv Argument vector
 * @return int Exit status
 */
int main(int argc, char* argv[]) {
    try {
        if (argc != 2) {
            throw std::runtime_error("Usage: " + std::string(argv[0]) + " <xyz_dir>");
        }

        std::string xyz_dir = argv[1];
        process_directory(xyz_dir);
    }
    catch (const std::exception& e) {
        std::cerr << "Error: " << e.what() << std::endl;
        return 1;
    }
    catch (...) {
        std::cerr << "Unknown error occurred." << std::endl;
        return 1;
    }

    return 0;
}
