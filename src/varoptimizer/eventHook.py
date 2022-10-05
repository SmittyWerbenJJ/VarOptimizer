
class EventHook(object):
    def __init__(self) -> None:
        self._handlers = []

    def __iadd__(self, handler):
        self._handlers.append(handler)
        return self

    def __isub__(self, handler):
        self._handlers.remove(handler)
        return self

    def fire(self, *args, **kwargs):
        for handler in self._handlers:
            if type(handler) is tuple:
                args = list(handler[1:])
                handler = handler[0]

            argCount = handler.__code__.co_argcount
            varnames = handler.__code__.co_varnames
            if argCount == 1 and "self" in varnames:
                handler()
            else:
                handler(*args, **kwargs)

    def clearObjectHandlers(self, inObject):
        for theHandler in self._handlers:
            if theHandler.im_self == inObject:
                self.unsubscribe(theHandler)
