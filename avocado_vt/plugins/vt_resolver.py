from avocado.core.nrunner import Runnable
from avocado.core.plugin_interfaces import Discoverer, Resolver
from avocado.core.resolver import (ReferenceResolution,
                                   ReferenceResolutionResult)
from avocado.core.settings import settings
from virttest.compat import get_opt

from ..discovery import DiscoveryMixIn


class VTResolverUtils(DiscoveryMixIn):

    def _parameters_to_runnable(self, params):
        params = self.convert_parameters(params)
        url = params.get('name')
        vt_params = params.get('vt_params')

        # Flatten the vt_params, discarding the attributes that are not
        # scalars, and will not be used in the context of nrunner
        for key in ('_name_map_file', '_short_name_map_file', 'dep'):
            if key in vt_params:
                del(vt_params[key])

        return Runnable('avocado-vt', url, **vt_params)

    def _get_reference_resolution(self, reference):
        self.config = settings.as_dict()
        try:
            cartesian_parser = self._get_parser()
            self._save_parser_cartesian_config(cartesian_parser)
        except Exception as details:
            return ReferenceResolution(reference,
                                       ReferenceResolutionResult.ERROR,
                                       info=details)
        if reference != '':
            cartesian_parser.only_filter(reference)

        runnables = [self._parameters_to_runnable(d) for d in
                     cartesian_parser.get_dicts()]
        if runnables:
            return ReferenceResolution(reference,
                                       ReferenceResolutionResult.SUCCESS,
                                       runnables)
        else:
            return ReferenceResolution(reference,
                                       ReferenceResolutionResult.NOTFOUND)


class VTResolver(Resolver, VTResolverUtils):

    name = 'vt'
    description = 'Test resolver for Avocado-VT tests'

    def resolve(self, reference):
        """
        It will resolve vt test references into resolutions.

        It discovers the tests from cartesian config based on the specification
        from the user.
        """
        return self._get_reference_resolution(reference)


class VTDiscoverer(Discoverer, VTResolverUtils):

    name = 'vt-discoverer'
    description = 'Test discoverer for Avocado-VT tests'

    def discover(self):
        """It will discover vt test resolutions from cartesian config."""
        self.config = settings.as_dict()
        if (not get_opt(self.config, 'vt.config') and
                not get_opt(self.config, 'list.resolver')):
            return ReferenceResolution('', ReferenceResolutionResult.NOTFOUND)

        return [self._get_reference_resolution('')]
