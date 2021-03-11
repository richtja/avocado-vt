#
# VERY VERY ROUGH PoC of Avocado-VT's Cartesian Config integration
# with Avocado's CIT varianter
#
# To use it, please follow the following steps
#
# 1) run: avocado list $YOUR_OTHER_ARGS --vt-save-config=/tmp/vt.config
# 2) select a test "prefix" and set it as FILTER_TEST_NAME
# 3) run this script
#
# It should generate a list of test names, picked from CIT's algorithm
# and, as long as they are actual test names (from the cartesian config
# PoV).
#
CONFIG_PATH = '/tmp/vt.config'
FILTER_TEST_NAME = 'type_specific.io-github-autotest-qemu.block_hotplug'
ARGS = ('only %s' % FILTER_TEST_NAME, )
ORDER_OF_COMBINATIONS = 3


import sys

from avocado_varianter_cit.Cit import Cit
from virttest.cartesian_config import Parser


def get_test_name(params):
    if "_short_name_map_file" in params:
        return params.get("_short_name_map_file")["subtests.cfg"]
    return params["shortname"]


def get_subtest_prefix(params):
    if "_name_map_file" in params:
        name = params.get("_name_map_file")["subtests.cfg"]
        parts = name.split(".")
        result = []
        for part in parts:
            if part.startswith("(subtest="):
                result.append(part[9:-1])
        return ".".join(result)


def get_parser(config_path, *args):
    parser = Parser(config_path)
    for arg in args:
        parser.parse_string(arg)
    return parser


def get_test_and_variants(test_dicts):
    test_and_variants = {}
    for test in test_dicts:
        prefix = get_subtest_prefix(test)
        name = get_test_name(test)
        assert name.startswith(prefix)
        variant = name[len(prefix)+1:]
        if prefix not in test_and_variants:
            test_and_variants[prefix] = []
        test_and_variants[prefix].append(variant)
    return test_and_variants


def variants_to_params_by_category(variants):
    """Turns the variants of a given test into parameters by category."""
    variants_split = [variant.split('.') for variant in variants]
    categories = zip(*variants_split)
    result = []
    for category in categories:
        result.append(set(category))
    return result


def categories_to_cit_parameters(categories):
    result = []
    for parameter_number, category in enumerate(categories, 1):
        result.append(("p%u" % parameter_number,
                       list(category)))
    return result


def compute_cit(parameters):
    """Compute the variations based on parameters

    Parameters is a list of tuples.  Each tuple contains the parameter
    name, and then the list of values.  Example:

    [('p1', ['raw', 'qcow2', 'virtio']),
     ('p2', ['max_size', 'fmt_qcow2', 'fmt_raw', 'default'])]
    """
    constraints = set()
    # shamelessly stolen from Cit plugin code
    input_data = [len(parameter[1]) for parameter in parameters]
    cit = Cit(input_data, ORDER_OF_COMBINATIONS, constraints)
    final_list = cit.compute()
    headers = [parameter[0] for parameter in parameters]  # pylint: disable=W0201
    results = [[parameters[j][1][final_list[i][j]] for j in range(len(final_list[i]))]
               for i in range(len(final_list))]
    variants = []  # pylint: disable=W0201
    for combination in results:
        variants.append(dict(zip(headers, combination)))
    return variants


def variants_to_vt_test_names(subtest_prefix, variants):
    """Puts together a list of vt test names based on prefix and variants."""
    result = []
    for variant in variants:
        this_variant_name = ".".join([variant[_] for _ in sorted(variant.keys())])
        result.append("%s.%s" % (subtest_prefix, this_variant_name))
    return result


def main():
    test_dicts = get_parser(CONFIG_PATH, *ARGS).get_dicts()
    test_and_variants = get_test_and_variants(test_dicts)
    variants = test_and_variants[FILTER_TEST_NAME]
    categories = variants_to_params_by_category(variants)
    cit_parameters = categories_to_cit_parameters(categories)
    variants = compute_cit(cit_parameters)

    # this remakes all the test names got from the cartesian config
    all_test_names = []
    for k in test_and_variants:
        for v in test_and_variants[k]:
            all_test_names.append("%s.%s" % (k, v))

    test_names = variants_to_vt_test_names(FILTER_TEST_NAME, variants)
    existing_test_names = [_ for _ in test_names if _ in all_test_names]

    print("\n".join(existing_test_names))


if __name__ == '__main__':
    main()
