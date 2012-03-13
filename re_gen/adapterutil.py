# Copyright (c) 2012
# Licensed under the terms of the MIT license; see LICENSE.txt

from zope.interface.adapter import AdapterRegistry
from zope.interface.interface import adapter_hooks, InterfaceClass
from zope.interface import Interface, implementedBy, providedBy
from zope.interface.common.sequence import IWriteSequence, IExtendedReadSequence

registry = AdapterRegistry()

class INumber(Interface):
    pass

class IInteger(INumber):
    pass

class IReal(INumber):
    pass

class IString(IExtendedReadSequence):
    pass

class IObjectSequence(IExtendedReadSequence):
    pass

class ITuple(IObjectSequence):
    pass

class IList(IObjectSequence, IWriteSequence):
    pass


fakeimplementeds = {
    int: IInteger,
    float: IReal,
    str: IString,
    list: IList,
    tuple: ITuple,
    set: ISet
}


def register(implementor, orig, *interfaceClasses):
    if orig in fakeimplementeds:
        origInterface = fakeimplementeds[orig]
    elif not isinstance(orig, InterfaceClass):
        origInterface = implementedBy(orig)
    else:
        origInterface = orig

    if not interfaceClasses:
        interfaceClasses = tuple(implementedBy(implementor))

    for interfaceClass in interfaceClasses:
        registry.register([origInterface], interfaceClass, '', implementor)

def adapter_for(orig, *interfaceClasses):
    def decorator(implementor):
        register(implementor, orig, *interfaceClasses)
        return implementor
    return decorator

def deregister(implementor, orig, *interfaceClasses):
    if not interfaceClasses:
        interfaceClasses = tuple(implementedBy(implementor))
    register(None, orig, *interfaceClasses)


def lookup(targetinterface, obj):
    try:
        sourceinterface = fakeimplementeds[type(obj)]
    except KeyError:
        sourceinterface = providedBy(obj)

    implementor = registry.lookup1(sourceinterface, targetinterface, '')

    if implementor == None:
        return None

    return implementor(obj)
adapter_hooks.append(lookup)