"""Latin square SD display mappings for DTT monitor UI."""

# Latin Square trial-name -> SD display number mappings
CONFIGURATION_TO_SD_NUMBER = {
    1: {
        "Manding": 1,
        "Receptive Instruction": 2,
        "Imitation": 3,
        "Tacting and Labeling": 4,
        "Emotion Labeling": 5,
        "Receptive Expression": 6,
    },
    2: {
        "Manding": 1,
        "Receptive Instruction": 4,
        "Imitation": 3,
        "Tacting and Labeling": 6,
        "Emotion Labeling": 5,
        "Receptive Expression": 2,
    },
    3: {
        "Manding": 1,
        "Receptive Instruction": 6,
        "Imitation": 3,
        "Tacting and Labeling": 2,
        "Emotion Labeling": 5,
        "Receptive Expression": 4,
    },
}

DEFAULT_CONFIGURATION = 1


def get_latin_square_mapping(configuration):
    """Return the trial-name -> SD display number mapping for a configuration."""

    try:
        config_key = int(configuration)
    except (TypeError, ValueError):
        config_key = DEFAULT_CONFIGURATION

    return CONFIGURATION_TO_SD_NUMBER.get(
        config_key,
        CONFIGURATION_TO_SD_NUMBER[DEFAULT_CONFIGURATION],
    )


def get_sd_display_number(trial_name, configuration):
    """Lookup the display number for a trial name in a given configuration."""
    return get_latin_square_mapping(configuration).get(trial_name)
