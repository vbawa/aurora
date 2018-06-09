from bravado.swagger_model import load_file
from bravado.client import CallableOperation, ResourceDecorator, SwaggerClient
import inspect
import os
import pdb

AUTH_TOKEN = os.environ["NANOLEAF_AUTH_TOKEN"]

# TODO: Edit the swagger.json file so that the parameter names are e.g. "brightness"
# instead of b, and then rejigger this to not use the first letter.
class WrappedCallableOp(CallableOperation):
    """ Wraps a callable operation to clean up the method names and add the
    authToken to every request. """
    def __init__(self, actual_callable_op, param_name):
        self.actual_callable_op = actual_callable_op
        # the parameter name is usually the first letter of the property name:
        # e.g., client.State.State_GetBrightness has param_name "b"
        self.param_name = param_name

    def __call__(self, *args, **kwargs):
        # TODO: Write resource-specific handlers so that I don't have to 
        kwargs["authToken"] = AUTH_TOKEN
        if len(args) == 1:
            kwargs[self.param_name] = args[0]
        if len(args) > 1:
            raise Exception("This shim doesn't know how to handle more than one arg")
        return self.actual_callable_op.__call__(**kwargs)

class WrappedResource(ResourceDecorator):
    """ Interceptor object for Resources: Authorization, Effects, Identify,
    State, PanelLayout, Info """
    def __init__(self, actual_resource, resource_name):
        self.actual_resource = actual_resource
        self.resource_name = resource_name

    def __getattr__(self, attr):
        """ Convert XxxxYyyy to Resource_XxxxYyyy, e.g. GetBrightness -->
        State_GetBrightness. The former is easier to use. """
        fixed_attr = "%s_%s" % (self.resource_name, attr)
        actual_callable_op = getattr(self.actual_resource, fixed_attr)
        param_name = attr.replace("Get", "").replace("Set", "")[0].lower()
        return WrappedCallableOp(actual_callable_op, param_name)
                                 

class NanoLeafClient(SwaggerClient):
    """ Weirdo class that both inherits from and is composed around
    SwaggerClient.  The former is for auto-complete and the latter is the
    actually-operable object, since this class overrides __getattr__ """
    @staticmethod
    def build(json_filename="swagger.json"):
        spec = load_file(json_filename)
        client = NanoLeafClient.from_spec(spec)
        client.swagger_client = SwaggerClient.from_spec(spec)
        return client

    def __getattr__(self, attr):
        """ Return a wrapped resource if a resource is requested or pass
        through to actual getattr. """
        actual_resource = getattr(self.swagger_client, attr)
        if attr in ["Authorization", "Effects", "Identify", "Info",
                "PanelLayout", "State"]:
            return WrappedResource(actual_resource, attr)
        else:
            return actual_resource
