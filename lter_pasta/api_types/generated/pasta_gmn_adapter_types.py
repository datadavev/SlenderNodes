# ./generated/pasta_gmn_adapter_types.py
# -*- coding: utf-8 -*-
# PyXB bindings for NM:e92452c8d3e28a9e27abfc9994d2007779e7f4c9
# Generated 2017-01-12 00:01:42.226848 by PyXB version 1.2.5 using Python 2.7.12.final.0
# Namespace AbsentNamespace0

from __future__ import unicode_literals
import pyxb
import pyxb.binding
import pyxb.binding.saxer
import io
import pyxb.utils.utility
import pyxb.utils.domutils
import sys
import pyxb.utils.six as _six
# Unique identifier for bindings created at the same time
_GenerationUID = pyxb.utils.utility.UniqueIdentifier('urn:uuid:f8c8c942-d894-11e6-9911-000c292ff10e')

# Version of PyXB used to generate the bindings
_PyXBVersion = '1.2.5'
# Generated bindings are not compatible across PyXB versions
if pyxb.__version__ != _PyXBVersion:
    raise pyxb.PyXBVersionError(_PyXBVersion)

# A holder for module-level binding classes so we can access them from
# inside class definitions where property names may conflict.
_module_typeBindings = pyxb.utils.utility.Object()

# Import bindings for namespaces imported into schema
import pyxb.binding.datatypes

# NOTE: All namespace declarations are reserved within the binding
Namespace = pyxb.namespace.CreateAbsentNamespace()
Namespace.configureCategories(['typeBinding', 'elementBinding'])

def CreateFromDocument (xml_text, default_namespace=None, location_base=None):
    """Parse the given XML and use the document element to create a
    Python instance.

    @param xml_text An XML document.  This should be data (Python 2
    str or Python 3 bytes), or a text (Python 2 unicode or Python 3
    str) in the L{pyxb._InputEncoding} encoding.

    @keyword default_namespace The L{pyxb.Namespace} instance to use as the
    default namespace where there is no default namespace in scope.
    If unspecified or C{None}, the namespace of the module containing
    this function will be used.

    @keyword location_base: An object to be recorded as the base of all
    L{pyxb.utils.utility.Location} instances associated with events and
    objects handled by the parser.  You might pass the URI from which
    the document was obtained.
    """

    if pyxb.XMLStyle_saxer != pyxb._XMLStyle:
        dom = pyxb.utils.domutils.StringToDOM(xml_text)
        return CreateFromDOM(dom.documentElement, default_namespace=default_namespace)
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    saxer = pyxb.binding.saxer.make_parser(fallback_namespace=default_namespace, location_base=location_base)
    handler = saxer.getContentHandler()
    xmld = xml_text
    if isinstance(xmld, _six.text_type):
        xmld = xmld.encode(pyxb._InputEncoding)
    saxer.parse(io.BytesIO(xmld))
    instance = handler.rootObject()
    return instance

def CreateFromDOM (node, default_namespace=None):
    """Create a Python instance from the given DOM node.
    The node tag must correspond to an element declaration in this module.

    @deprecated: Forcing use of DOM interface is unnecessary; use L{CreateFromDocument}."""
    if default_namespace is None:
        default_namespace = Namespace.fallbackNamespace()
    return pyxb.binding.basis.element.AnyCreateFromDOM(node, default_namespace)


# Complex type [anonymous] with content type ELEMENT_ONLY
class CTD_ANON (pyxb.binding.basis.complexTypeDefinition):
    """Complex type [anonymous] with content type ELEMENT_ONLY"""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 8, 8)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element taskId uses Python identifier taskId
    __taskId = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'taskId'), 'taskId', '__AbsentNamespace0_CTD_ANON_taskId', False, pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 10, 16), )

    
    taskId = property(__taskId.value, __taskId.set, None, None)

    
    # Element status uses Python identifier status
    __status = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'status'), 'status', '__AbsentNamespace0_CTD_ANON_status', False, pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 11, 16), )

    
    status = property(__status.value, __status.set, None, None)

    
    # Element pid uses Python identifier pid
    __pid = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'pid'), 'pid', '__AbsentNamespace0_CTD_ANON_pid', False, pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 12, 16), )

    
    pid = property(__pid.value, __pid.set, None, None)

    
    # Element sourceNode uses Python identifier sourceNode
    __sourceNode = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'sourceNode'), 'sourceNode', '__AbsentNamespace0_CTD_ANON_sourceNode', False, pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 13, 16), )

    
    sourceNode = property(__sourceNode.value, __sourceNode.set, None, None)

    
    # Element timestamp uses Python identifier timestamp
    __timestamp = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'timestamp'), 'timestamp', '__AbsentNamespace0_CTD_ANON_timestamp', False, pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 14, 16), )

    
    timestamp = property(__timestamp.value, __timestamp.set, None, None)

    _ElementMap.update({
        __taskId.name() : __taskId,
        __status.name() : __status,
        __pid.name() : __pid,
        __sourceNode.name() : __sourceNode,
        __timestamp.name() : __timestamp
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.CTD_ANON = CTD_ANON


# Complex type [anonymous] with content type ELEMENT_ONLY
class CTD_ANON_ (pyxb.binding.basis.complexTypeDefinition):
    """Defines a structure for serializing PASTA GMN Adapter Exceptions."""
    _TypeDefinition = None
    _ContentTypeTag = pyxb.binding.basis.complexTypeDefinition._CT_ELEMENT_ONLY
    _Abstract = False
    _ExpandedName = None
    _XSDLocation = pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 25, 6)
    _ElementMap = {}
    _AttributeMap = {}
    # Base type is pyxb.binding.datatypes.anyType
    
    # Element description uses Python identifier description
    __description = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'description'), 'description', '__AbsentNamespace0_CTD_ANON__description', False, pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 27, 10), )

    
    description = property(__description.value, __description.set, None, None)

    
    # Element trace uses Python identifier trace
    __trace = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'trace'), 'trace', '__AbsentNamespace0_CTD_ANON__trace', False, pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 28, 10), )

    
    trace = property(__trace.value, __trace.set, None, None)

    
    # Element package_id uses Python identifier package_id
    __package_id = pyxb.binding.content.ElementDeclaration(pyxb.namespace.ExpandedName(None, 'package_id'), 'package_id', '__AbsentNamespace0_CTD_ANON__package_id', False, pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 29, 10), )

    
    package_id = property(__package_id.value, __package_id.set, None, None)

    _ElementMap.update({
        __description.name() : __description,
        __trace.name() : __trace,
        __package_id.name() : __package_id
    })
    _AttributeMap.update({
        
    })
_module_typeBindings.CTD_ANON_ = CTD_ANON_


setting = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'setting'), pyxb.binding.datatypes.string, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 19, 4))
Namespace.addCategoryObject('elementBinding', setting.name().localName(), setting)

replicationRequest = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'replicationRequest'), CTD_ANON, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 7, 4))
Namespace.addCategoryObject('elementBinding', replicationRequest.name().localName(), replicationRequest)

adapterError = pyxb.binding.basis.element(pyxb.namespace.ExpandedName(Namespace, 'adapterError'), CTD_ANON_, documentation='Defines a structure for serializing PASTA GMN Adapter Exceptions.', location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 21, 4))
Namespace.addCategoryObject('elementBinding', adapterError.name().localName(), adapterError)



CTD_ANON._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'taskId'), pyxb.binding.datatypes.unsignedLong, scope=CTD_ANON, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 10, 16)))

CTD_ANON._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'status'), pyxb.binding.datatypes.string, scope=CTD_ANON, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 11, 16)))

CTD_ANON._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'pid'), pyxb.binding.datatypes.string, scope=CTD_ANON, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 12, 16)))

CTD_ANON._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'sourceNode'), pyxb.binding.datatypes.string, scope=CTD_ANON, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 13, 16)))

CTD_ANON._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'timestamp'), pyxb.binding.datatypes.dateTime, scope=CTD_ANON, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 14, 16)))

def _BuildAutomaton ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton
    del _BuildAutomaton
    import pyxb.utils.fac as fac

    counters = set()
    states = []
    final_update = None
    symbol = pyxb.binding.content.ElementUse(CTD_ANON._UseForTag(pyxb.namespace.ExpandedName(None, 'taskId')), pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 10, 16))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(CTD_ANON._UseForTag(pyxb.namespace.ExpandedName(None, 'status')), pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 11, 16))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(CTD_ANON._UseForTag(pyxb.namespace.ExpandedName(None, 'pid')), pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 12, 16))
    st_2 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    final_update = None
    symbol = pyxb.binding.content.ElementUse(CTD_ANON._UseForTag(pyxb.namespace.ExpandedName(None, 'sourceNode')), pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 13, 16))
    st_3 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_3)
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(CTD_ANON._UseForTag(pyxb.namespace.ExpandedName(None, 'timestamp')), pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 14, 16))
    st_4 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_4)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
         ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_3, [
         ]))
    st_2._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_4, [
         ]))
    st_3._set_transitionSet(transitions)
    transitions = []
    st_4._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
CTD_ANON._Automaton = _BuildAutomaton()




CTD_ANON_._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'description'), pyxb.binding.datatypes.string, scope=CTD_ANON_, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 27, 10)))

CTD_ANON_._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'trace'), pyxb.binding.datatypes.string, scope=CTD_ANON_, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 28, 10)))

CTD_ANON_._AddElement(pyxb.binding.basis.element(pyxb.namespace.ExpandedName(None, 'package_id'), pyxb.binding.datatypes.string, scope=CTD_ANON_, location=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 29, 10)))

def _BuildAutomaton_ ():
    # Remove this helper function from the namespace after it is invoked
    global _BuildAutomaton_
    del _BuildAutomaton_
    import pyxb.utils.fac as fac

    counters = set()
    cc_0 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 28, 10))
    counters.add(cc_0)
    cc_1 = fac.CounterCondition(min=0, max=1, metadata=pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 29, 10))
    counters.add(cc_1)
    states = []
    final_update = set()
    symbol = pyxb.binding.content.ElementUse(CTD_ANON_._UseForTag(pyxb.namespace.ExpandedName(None, 'description')), pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 27, 10))
    st_0 = fac.State(symbol, is_initial=True, final_update=final_update, is_unordered_catenation=False)
    states.append(st_0)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_0, False))
    symbol = pyxb.binding.content.ElementUse(CTD_ANON_._UseForTag(pyxb.namespace.ExpandedName(None, 'trace')), pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 28, 10))
    st_1 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_1)
    final_update = set()
    final_update.add(fac.UpdateInstruction(cc_1, False))
    symbol = pyxb.binding.content.ElementUse(CTD_ANON_._UseForTag(pyxb.namespace.ExpandedName(None, 'package_id')), pyxb.utils.utility.Location('/home/dahl/d1-git/SlenderNodes/lter_pasta/api_types/schemas/pasta_gmn_adapter_types.xsd', 29, 10))
    st_2 = fac.State(symbol, is_initial=False, final_update=final_update, is_unordered_catenation=False)
    states.append(st_2)
    transitions = []
    transitions.append(fac.Transition(st_1, [
         ]))
    transitions.append(fac.Transition(st_2, [
         ]))
    st_0._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_1, [
        fac.UpdateInstruction(cc_0, True) ]))
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_0, False) ]))
    st_1._set_transitionSet(transitions)
    transitions = []
    transitions.append(fac.Transition(st_2, [
        fac.UpdateInstruction(cc_1, True) ]))
    st_2._set_transitionSet(transitions)
    return fac.Automaton(states, counters, False, containing_state=None)
CTD_ANON_._Automaton = _BuildAutomaton_()

