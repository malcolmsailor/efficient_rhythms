from .. import er_constants
from .settings_postprocess import SettingsPostprocessor as ERSettings


def merge_settings(settings_paths, silent=True):
    def _merge(dict1, dict2):
        for key, val in dict2.items():
            if (
                isinstance(val, dict)
                and key in dict1
                and isinstance(dict1[key], dict)
            ):
                _merge(dict1[key], val)
                dict2[key] = dict1[key]
        dict1.update(dict2)

    merged_dict = {}
    for user_settings_path in settings_paths:
        if not silent:
            print(f"Reading settings from {user_settings_path}")
        with open(user_settings_path, "r", encoding="utf-8") as inf:
            user_settings = eval(inf.read(), vars(er_constants))
        _merge(merged_dict, user_settings)
    return merged_dict


def read_in_settings(
    settings_input,
    settings_class,
    silent=False,
    output_path=None,
    randomize=False,
    seed=None,
):
    if settings_input is None:
        settings_input = {}
    if isinstance(settings_input, dict):
        settings_dict = settings_input
    else:
        settings_dict = merge_settings(settings_input, silent=silent)
    if output_path is not None:
        settings_dict["output_path"] = output_path
    if seed is not None:
        settings_dict["seed"] = seed
    if randomize:
        settings_dict["_randomized"] = True
        settings_dict["_user_settings"] = settings_input
    settings_dict["_silent"] = silent
    return settings_class(**settings_dict)


def get_settings(
    user_settings,
    random_settings=False,
    seed=None,
    silent=False,
    output_path=None,
):
    # TODO set seed here
    er = read_in_settings(
        user_settings,
        ERSettings,
        silent=silent,
        output_path=output_path,
        randomize=random_settings,
        seed=seed,
    )
    return er
