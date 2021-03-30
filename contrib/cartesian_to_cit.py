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
import itertools

CONFIG_PATH = '/tmp/vt.config'
FILTER_TEST_NAME = 'type_specific.io-github-autotest-qemu.block_hotplug'
ARGS = ('only %s' % FILTER_TEST_NAME, )
ORDER_OF_COMBINATIONS = 3

DEFAULT_VALUE = ""


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
    categories = itertools.zip_longest(*variants_split, fillvalue=DEFAULT_VALUE)
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


def compute_cit(parameters, constraints):
    """Compute the variations based on parameters

    Parameters is a list of tuples.  Each tuple contains the parameter
    name, and then the list of values.  Example:

    [('p1', ['raw', 'qcow2', 'virtio']),
     ('p2', ['max_size', 'fmt_qcow2', 'fmt_raw', 'default'])]
    """
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
        this_variant_name = ".".join([variant[_] for _ in sorted(variant.keys())
                                      if variant[_] != DEFAULT_VALUE])
        result.append("%s.%s" % (subtest_prefix, this_variant_name))
    return result


def get_constraints(variants, categories):

    def _exists(combination):
        """Checks if the combination is part of valid variant"""
        for var in variants_split:
            is_valid = True
            for index, value in combination:
                if var[index] != value:
                    is_valid = False
            if is_valid:
                return True
        return False

    def _reformat_constraint(combination):
        """Converts the combination into the known format for CIT plugin"""
        constraint = []
        for i, comb in combination:
            constraint.append((i, tuple(categories[i]).index(comb)))
        return tuple(sorted(constraint, key=lambda x: int(x[0])))

    def _simplify_constraint(constraint):
        """Finds the exact values which are responsible for invalidity of
        the combination. Those values will be used as constraints.
        """
        constraint_copy = constraint.copy()
        last_value = constraint_copy.pop()
        index = 0
        constraint_found = False
        while index != len(constraint_copy) and not constraint_found:
            index = index + 1
            for comb in itertools.combinations(constraint_copy, index):
                comb = list(comb)
                comb.append(last_value)
                if not _exists(comb):
                    constraints.append(_reformat_constraint(comb))
                    constraint_found = True

    def _compute(combination, index):
        """Search for invalid combination. It assumes that most of the
        constrained values are in the last parameter because the parameters are
        created from the tree.
        """
        if _exists(combination):
            if index != 0:
                for value in categories[index]:
                    combination_copy = combination.copy()
                    combination_copy.append((index, value))
                    _compute(combination_copy, index-1)
        else:
            _simplify_constraint(combination)

    constraints = []
    # converts variants from string to nxn matrix uses DEFAULT_VALUE for blank cells
    variants_split = []
    for variant in variants:
        split = variant.split('.')
        if len(split) < len(categories):
            split.extend([DEFAULT_VALUE] * (len(categories)-len(split)))
        variants_split.append(tuple(split))

    for value in categories[-1]:
        combination = [(len(categories)-1, value)]
        index = len(categories)-2
        _compute(combination, index)

    return set(constraints)


def test_validity(variants, posible_variants):
    for variant in variants:
        if variant not in posible_variants:
            return False
    return True


def main():
    test_dicts = get_parser(CONFIG_PATH, *ARGS).get_dicts()
    test_and_variants = get_test_and_variants(test_dicts)
    variants = test_and_variants[FILTER_TEST_NAME]
    categories = variants_to_params_by_category(variants)
    cit_parameters = categories_to_cit_parameters(categories)
    constraints = get_constraints(variants, categories)
    variants = compute_cit(cit_parameters, constraints)

    # this remakes all the test names got from the cartesian config
    all_test_names = []
    for k in test_and_variants:
        for v in test_and_variants[k]:
            all_test_names.append("%s.%s" % (k, v))

    test_names = variants_to_vt_test_names(FILTER_TEST_NAME, variants)
    # existing_test_names = [_ for _ in test_names if _ in all_test_names]
    if test_validity(test_names, all_test_names):
        print("Found %s tests:\n" % len(test_names))
        print("\n".join(test_names))


if __name__ == '__main__':
    main()
