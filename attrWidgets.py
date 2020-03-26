# 	Trevor Sommer: trevor@trevorsommer.com
#	Version - 1.0.0
#	
# ----------------------------------------------------------------------------------------------------
# DESCRIPTION
# ----------------------------------------------------------------------------------------------------
##  @file   attrWidgets.py
#   @brief  Pyside widgets for attribute controls within Maya. 
#       ---- Each Widget has the ability to connect to a plug and be driven, or drive that attributes value simp[le "setLiveMode" to True
#       ---- The widgets all emit a "valueChanged" signal when there value is updated
#       ---- You can steal or set the attributes current data via the "stealMyData" or "pushInData" functions
#       ---- SpinBox widgets attempt to set their limits based on the soft ranges of the given plugs
#       ---- Enum or option type attributes should give all there options as available members of a combo box
#
#   @note   Some of this is taken and modified from the Maya devKit connectAttr.py
#
#   Copyright 2015 Autodesk, Inc. All rights reserved.
# 
#   Use of this software is subject to the terms of the Autodesk
#   license agreement provided at the time of installation or download,
#   or which otherwise accompanies this software in either electronic
#   or hard copy form.
#

import sys, os, types
import logging, weakref

from PySide2 import QtCore as QtCore
from PySide2 import QtGui as QtGui
from PySide2 import QtWidgets as QtWidgets
from PySide2 import QtUiTools

from maya import cmds
from maya import mel
from maya import OpenMaya as om
from maya import OpenMayaUI as omui 

##  @brief create logger object for Module
_logger = logging.getLogger(__name__)
_logger.setLevel(logging.WARNING)

'''-------------------------------------
Attribute Widget defaults/Globals
-------------------------------------'''
##  @brief  Float Attribute Widget Default Step increment
#   @note Widget is Locked off to 3 decimals 0.001
K_FLOAT_WIDGET_STEP_INCREMENT   = 0.01    

##  @brief  Float Attribute Widget slider Factor.
#   @note higher factor means more accuracy
K_FLOAT_WIDGET_FACTOR           = int(100)

##  @brief  Integer SpinBox and slider increment
K_INTEGER_WIDGET_STEP_INCREMENT = 1

##  @brief  Integer attribute Widget default values
K_INTEGER_ATTR_DEFAULTS =   {
                            'value': 0,
                            'minimum':0,
                            'maximum':10000,
                            'softRange':[0,10000]
                            }

##  @brief  Float attribute Widget default values
K_FLOAT_ATTR_DEFAULTS   =   {
                            'value': 0.0,
                            'minimum':0.0,
                            'maximum':10000.0,
                            'softRange':[0.0,10000.0]
                            }

##  @brief  String attribute Widget default values
K_STRING_ATTR_DEFAULTS  = {'value':''}

##  @brief storage key for override nodes plug {ovrNode}.{attr}
K_OVR_PLUG_OVERRIDE_DATA_KEYS           = 'overridePlug'


##  @brief Splits a node.plug string and returns the node part only
#
#   @param plugString [str] - MayaNode.attribute
#
#   @retval [str] - Node name from plug
#
def getNodeFromPlugString(plugString):
    try:
        return splitPlugString(plugString)[0]
    except Exception as err:
        return None
        
##  @brief Maya Callback Utility Class, From the Maya devKit connectAttr.py Example
#
class MCallbackIdWrapper(object):
    '''Wrapper class to handle cleaning up of MCallbackIds from registered MMessage
    '''
    def __init__(self, callbackId):
        super(MCallbackIdWrapper, self).__init__()
        self.callbackId = callbackId

    def __del__(self):
        om.MMessage.removeCallback(self.callbackId)

    def __repr__(self):
        return 'MCallbackIdWrapper(%r)'%self.callbackId

##  @brief Utility to get the depend node from a a name string for Callback Creation, From the Maya devKit connectAttr.py Example
#
def _getDependNode(nodeName):
    """Get an MObject (depend node) for the associated node name

    :Parameters:
        nodeName
            String representing the node
    
    :Return: depend node (MObject)

    """
    dependNode = om.MObject()
    selList = om.MSelectionList()
    selList.add(nodeName)
    if selList.length() > 0: 
        selList.getDependNode(0, dependNode)
    return dependNode

##  @brief this QComboBox scrolls only if opend before. 
#   if the mouse is over the QComboBox and the mousewheel is turned,
#   the mousewheel event of the scrollWidget is triggered
#
class CustomQComboBox(QtWidgets.QComboBox):
    def __init__(self, scrollWidget=None, *args, **kwargs):
        super(CustomQComboBox, self).__init__(*args, **kwargs)  
        self.scrollWidget=scrollWidget
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus():
            return QtWidgets.QComboBox.wheelEvent(self, *args, **kwargs)
        '''
        else:
            return self.scrollWidget.wheelEvent(*args, **kwargs)
        '''

##  @brief this QSlider scrolls only if opend before. 
#   if the mouse is over the QSlider and the mousewheel is turned,
#   the mousewheel event of the scrollWidget is triggered
#
class CustomQSlider(QtWidgets.QSlider):
    def __init__(self, scrollWidget=None, *args, **kwargs):
        super(CustomQSlider, self).__init__(*args, **kwargs)  
        self.scrollWidget=scrollWidget
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus():
            return QtWidgets.QSlider.wheelEvent(self, *args, **kwargs)
        #else:
        #    return self.scrollWidget.wheelEvent(*args, **kwargs)

##  @brief this QDoubleSpinBox scrolls only if opend before. 
#   if the mouse is over the QDoubleSpinBox and the mousewheel is turned,
#   the mousewheel event of the scrollWidget is triggered
#
class CustomQDoubleSpinBox(QtWidgets.QDoubleSpinBox):
    def __init__(self, scrollWidget=None, *args, **kwargs):
        super(CustomQDoubleSpinBox, self).__init__(*args, **kwargs)  
        self.scrollWidget=scrollWidget
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus():
            return QtWidgets.QDoubleSpinBox.wheelEvent(self, *args, **kwargs)
        else:
            return self.scrollWidget.wheelEvent(*args, **kwargs)

##  @brief this QSpinBox scrolls only if opend before. 
#   if the mouse is over the QSpinBox and the mousewheel is turned,
#   the mousewheel event of the scrollWidget is triggered
#
class CustomQSpinBox(QtWidgets.QSpinBox):
    def __init__(self, scrollWidget=None, *args, **kwargs):
        super(CustomQSpinBox, self).__init__(*args, **kwargs)  
        self.scrollWidget=scrollWidget
        self.setFocusPolicy(QtCore.Qt.StrongFocus)

    def wheelEvent(self, *args, **kwargs):
        if self.hasFocus():
            return QtWidgets.QSpinBox.wheelEvent(self, *args, **kwargs)
        #else:
        #    return self.scrollWidget.wheelEvent(*args, **kwargs)


##  @brief This is the base attribute widget class\n 
#
#   it will be subClassed by "type" for Dynamic Attribute widget creation\n
#   It contains logic for "connecting" itself to maya scene objects via callbacks\n
#   It also has Properties for Quick reference of its key protected attributes\n
#
class BaseAttributeWidget(QtWidgets.QWidget):

    valueChanged = QtCore.Signal()

    VALID_ATTR_TYPES = set()
    ALWAYS_SKIP_PROPERTIES = ['valueChanged', 'staticMetaObject', 'VALID_ATTR_TYPES', 'PUSH_SKIP_PROPERTIES', 'GARBAGE_TEST']
    PUSH_SKIP_PROPERTIES = ['node','attribute','attributeType','isConnected','plugString']
    GARBAGE_TEST = 'GAdbsdbrhad'

    def __init__(self, parent=None, node=None, attribute=None, attributeType=None, **kwargs):
        super(BaseAttributeWidget, self).__init__(parent=parent)

        if not node or not attribute or not attributeType:
            raise TypeError('Unable to initialize custom attribute widget without proper valid arguments\n  node: "{}"\n    attribute: "{}"\n   attributeType: "{}"\n'.format(node, attribute, attributeType))

        self._node          = node
        self._attribute     = attribute
        self._plugString    = '{}.{}'.format(self._node, self._attribute)
        self._displayName   =  kwargs.get('displayName', None)

        if cmds.getAttr(self._plugString, type=True) != attributeType:
            raise TypeError('Given Plug "{}" is of improper Given Type: {}'.format(self._plugString, attributeType))

        self._attributeType = attributeType
        if self._attributeType not in self.VALID_ATTR_TYPES:
            raise TypeError('Invalid attribute Type passed, type is not supported by this widget: {}'.format(attributeType))

        self._isConnected               = False
        self._attributeDefaults         = self._getAttributeInformation()
        self._value                     = kwargs.get('value', self._attributeDefaults['value'])
        self._customIncrement           = kwargs.get('increment', K_FLOAT_WIDGET_STEP_INCREMENT)

        self._deferredUpdateRequest     = list()
        self._nodeCallbacks             = list() 
        self._sceneAttributeData   = dict()

        self._buildWidget(**kwargs)
        self._setupSocketConnections()
    
    def wheelEvent(self, event):
        pass

    '''-------------------------
    ## Class Properties
    -------------------------'''
    @property 
    def node(self):
        return self._node
    @property 
    def attribute(self):
        return self._attribute
    @property 
    def attributeType(self):
        return self._attributeType
    @property 
    def isConnected(self):
        return self._isConnected
    @property 
    def plugString(self):
        return self._plugString

    @property
    def value(self):
        return self._value
    @value.setter
    def value(self, val):
        self._value = val
        self._onSetAttr()
        self._updateWidgetValues()

    '''-------------------------
    ## Private Methods
    -------------------------'''
    def _onGetAttr(self):
        if not self._isConnected:
            return 

        if self._sceneAttributeData:
            if not self._sceneAttributeData.get(K_OVR_PLUG_OVERRIDE_DATA_KEYS, None):
                return 
            _val = cmds.getAttr(self._sceneAttributeData[K_OVR_PLUG_OVERRIDE_DATA_KEYS])
        else:
            _val = cmds.getAttr(self._plugString)
        if not _val:
            return 

        _logger.info('_processDeferredUpdateRequest Plug -- "{}" == {}'.format(self._plugString, _val))
        self._value = _val
        self._updateWidgetValues()
        return _val

    def _onSetAttr(self, force=False):
        '''Handle setting the attribute when the UI widget edits the value for it.
        If it fails to set the value, then restore the original value to the UI widget
        '''
        if not force:
            if not self._isConnected:
                #NOTE: if not set to connect or if live mode is not enabled do nothing
                return

        if self._sceneAttributeData:
            if not self._sceneAttributeData.get(K_OVR_PLUG_OVERRIDE_DATA_KEYS, None):
                return
            _plugString = self._sceneAttributeData[K_OVR_PLUG_OVERRIDE_DATA_KEYS]
        else:
            _plugString = self._plugString

        _val = cmds.getAttr(self._plugString)   
        try:
            if self._attributeType == 'string':
                cmds.setAttr(_plugString, self._value, type=self._attributeType)
            else:
                cmds.setAttr(_plugString, self._value)
        except Exception as err:
            _logger.warning(err)
            _logger.info('Unable to set node attribute in file, Slider for "{}" is now out of sync'.format(_plugString))
            #NOTE: we can't do the following without causing a terrible loop
            #_curSceneVal = cmds.getAttr(self._plugString)
            #self._value = _curSceneVal

    def _onDirtyPlug(self, node, plug, *args, **kwargs):
        '''Add to the self._deferredUpdateRequest member variable that is then 
        deferred processed by self._processDeferredUpdateRequest(). 
        '''
        # get long name of the attr, to use as the dict key
        attrName = plug.partialName(False, False, False, False, False, True)
        # get node.attr string
        nodePlugString = plug.partialName(True, False, False, False, False, True) 

        # get node.attr string
        nodePlugString = plug.partialName(True, False, False, False, False, True) 

        # Add to the dict of widgets to defer update
        self._deferredUpdateRequest.append(True)

        # Trigger an evalDeferred action if not already done
        if len(self._deferredUpdateRequest) == 1:
            cmds.evalDeferred(self._processDeferredUpdateRequest, low=True)

    def _processDeferredUpdateRequest(self):
        '''Retrieve the attr value and set the widget value
        '''
        if self._deferredUpdateRequest:
            self._onGetAttr()
        self._deferredUpdateRequest = list()

    def _buildWidget(self, **kwargs):
        pass

    def _setupSocketConnections(self):
        pass

    def _updateWidgetValues(self):
        self.valueChanged.emit()

    def _widgetUpdated(self):
        self.valueChanged.emit()

    def _findOverrideNodeForLayer(self, renderLayerName):
        pass

    def _getAttributeInformation(self):
        _attrData = dict()
        return _attrData

    def _getAllProperties(self):
        validAttrs=[]
        localAttributes = vars(self.__class__)
        for attr in localAttributes:
            if attr.startswith('_'):
                continue
            if isinstance(localAttributes[attr], types.FunctionType) or isinstance(localAttributes[attr], types.MethodType):
                continue
            if isinstance(localAttributes[attr], property) and attr not in self.ALWAYS_SKIP_PROPERTIES:
                validAttrs.append(attr)

        ##NOTE: This class needs a deep search for props in all parent classes too                
        parentClasses = list(self.__class__.__bases__)
        for parent in parentClasses:
            parentAttributes = vars(parent)
            for attr in parentAttributes:
                if attr in validAttrs: 
                    continue
                if attr.startswith('_'):
                    continue
                if isinstance(parentAttributes[attr], types.FunctionType) or isinstance(parentAttributes[attr], types.MethodType):
                    continue
                if not isinstance(parentAttributes[attr], property) or attr in self.ALWAYS_SKIP_PROPERTIES:
                    continue
                if attr not in validAttrs:
                    validAttrs.append(attr)
        return validAttrs

    '''-------------------------
    ## Public Methods 
    -------------------------'''
    def connectToNode(self, pull=False):
        '''Connect UI to the specified node, or override
        '''
        self._nodeCallbacks = list()
        self._deferredUpdateRequest=list()

        if self._isConnected:
            #NOTE: if not set to connect or if live mode is not enabled do nothing
            return

        if self._sceneAttributeData:
            if not self._sceneAttributeData.get(K_OVR_PLUG_OVERRIDE_DATA_KEYS, None):
                return 
            _plugString = self._sceneAttributeData[K_OVR_PLUG_OVERRIDE_DATA_KEYS]
            
        else:
            _plugString = self._plugString
        
        if not cmds.objExists(_plugString):
            return 
        if self._attributeType not in self.VALID_ATTR_TYPES:
            return 
        _node = getNodeFromPlugString(_plugString)

        if pull:
            _value=None
            try:
                _value = self._onGetAttr()
            except Exception as err:
                _logger.warning('Attribute Setup Aborted Something went array when Querying the value for following plug: "{}"'.format(self._plugString))
                return 

            self.value = _value
        else:
            #NOTE: if not pulling the value we are pushing our current value down to the node
            self._onSetAttr(force=True)

        # Note: addNodeDirtyPlugCallback better than addAttributeChangedCallback
        # for UI since the 'dirty' check will always refresh the value of the attr
        _nodeObj = _getDependNode(_node)
        _cb = om.MNodeMessage.addNodeDirtyPlugCallback(_nodeObj, self._onDirtyPlug, None)
        self._nodeCallbacks.append( MCallbackIdWrapper(_cb) )

        self._isConnected = True

    def disConnectFromNode(self):
        if not self._isConnected:
            return 

        #NOTE: Make sure this widgets value is in sync with what in the file
        self._onGetAttr()

        #NOTE: Set the Connected var
        self._isConnected = False

        #NOTE: Then remove any callback this class may have registered
        for _callback in self._nodeCallbacks:
            del _callback

    def setLiveMode(self, state):
        if state == self.isConnected:
            return 

        if state:
            self.connectToNode()
        else:
            self.disConnectFromNode()

    def stealMyData(self):
        _returnData=dict()
        if self._sceneAttributeData:
            _returnData=dict(self._sceneAttributeData)

        _allProperties = self._getAllProperties()
        for _prop in _allProperties:
            _returnData[_prop] = getattr(self, _prop)
        return _returnData

    def pushInData(self, data):
        if not data:
            self.resetToDefaultValue()
            return 
            
        self._sceneAttributeData = data
        _allProperties = self._getAllProperties()
        for _prop in _allProperties:
            if _prop in self.PUSH_SKIP_PROPERTIES:
                continue
            if data.get(_prop, self.GARBAGE_TEST) != self.GARBAGE_TEST:
                setattr(self, _prop, data[_prop])
                continue

    def resetToDefaultValue(self):
        if self._attributeDefaults.get('value', 'dhgwsdbsadbsdb') != 'dhgwsdbsadbsdb':
            self.value = self._attributeDefaults['value']

##  @brief String Attrribute Class Widget, with Label and lineEdit.
#
class StringAttributeWidget(BaseAttributeWidget):

    VALID_ATTR_TYPES = set(['string'])


    def __init__(self, parent=None, node=None, attribute=None, attributeType=None, **kwargs):
        super(StringAttributeWidget, self).__init__(
                                                    parent=parent, 
                                                    node=node, 
                                                    attribute=attribute, 
                                                    attributeType=attributeType, 
                                                    **kwargs
                                                    )

    def _getAttributeInformation(self):
        _attrData = {'value':''}
        if not cmds.objExists(str(self.plugString)):
            return _attrData
        _attrData['value'] = cmds.getAttr(self.plugString)
        return _attrData

    def _buildWidget(self, **kwargs):
        _val        =   self._attributeDefaults['value']
        self._value = _val

        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        self.main_layout.setContentsMargins(QtCore.QMargins(0,0,0,0))

        self.setLayout(self.main_layout)

        #NOTE: Need a Qlabel
        _useName = str(self._attribute).capitalize()
        if self._displayName:
            _useName=self._displayName
        self._label = QtWidgets.QLabel(_useName)
        self._label.setScaledContents(False)
        self._label.setMinimumWidth(125)
        self._label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)

        #NOTE: Need a QLineEdit
        self._lineEdit= QtWidgets.QLineEdit(self)
        self._lineEdit.setText(_val)

        self.main_layout.addWidget(self._label)
        self.main_layout.addWidget(self._lineEdit)
        self.main_layout.addSpacerItem(
                                        QtWidgets.QSpacerItem(   
                                                            10, 
                                                            10, 
                                                            QtWidgets.QSizePolicy.Expanding, 
                                                            QtWidgets.QSizePolicy.Expanding
                                                            )
                                        )

    def _setupSocketConnections(self):
        self._lineEdit.textChanged.connect(self._widgetUpdated)

    def _updateWidgetValues(self):
        if self._value != self._lineEdit.text():
            self._lineEdit.textChanged.disconnect(self._widgetUpdated)
            self._lineEdit.setText(self._value)
            self._lineEdit.textChanged.connect(self._widgetUpdated)
        super(StringAttributeWidget, self)._updateWidgetValues()

    def _widgetUpdated(self):
        self._value = self._lineEdit.text()
        self._onSetAttr()
        super(StringAttributeWidget, self)._widgetUpdated()

##  @brief Enum Attribute Class Widget, with Label and Combo Box, 
#   auto fills in with in scene value is it can find the plug
#
class EnumAttributeWidget(BaseAttributeWidget):

    VALID_ATTR_TYPES = set(['enum'])

    def __init__(self, parent=None, node=None, attribute=None, attributeType=None, **kwargs):
        self._enumValues = kwargs.get('enumStrings', list())
        super(EnumAttributeWidget, self).__init__(
                                                parent=parent, 
                                                node=node, 
                                                attribute=attribute, 
                                                attributeType=attributeType, 
                                                **kwargs
                                                )

    @property
    def enumValues(self):
        return self._enumValues
    @enumValues.setter
    def enumValues(self, val):
        if not isinstance(val, list):
            raise TypeError('Unable to set enumValues with anything other than a list')
        if val != self._enumValues:
            for _idx in xrange(self._comboBox.count()-1):
                self._comboBox.removeItem(_idx)
            self._comboBox.addItems(val)
            self._enumValues = val
            self._comboBox.addItems(self._enumValues)
            self._comboBox.setCurrentIndex(self.value)

    def _getAttributeInformation(self):
        _attrData = {'value':False}
        if not cmds.objExists(str(self.plugString)):
            return _attrData

        _existingEnums = cmds.attributeQuery(self.attribute, node=self.node, listEnum=True)
        _enumStrings = _existingEnums[0].split(':')
        _attrData['enumStrings'] = _enumStrings
        
        _attrData['value'] = cmds.getAttr(self.plugString)
        return _attrData

    def _buildWidget(self, **kwargs):

        _val        =   self._attributeDefaults['value']
        self._value = _val
        self._enumValues = self._attributeDefaults['enumStrings']

        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        self.main_layout.setContentsMargins(QtCore.QMargins(0,0,0,0))

        self.setLayout(self.main_layout)

        #NOTE: Need a Qlabel
        _useName = str(self._attribute).capitalize()
        if self._displayName:
            _useName=self._displayName
        self._label = QtWidgets.QLabel(_useName)
        self._label.setScaledContents(False)
        self._label.setMinimumWidth(125)
        self._label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)

        #NOTE: Need a QComboBox
        self._comboBox = CustomQComboBox(self)
        self._comboBox.addItems(list(self._enumValues))
        self._comboBox.setCurrentIndex(_val)

        self.main_layout.addWidget(self._label)
        self.main_layout.addWidget(self._comboBox)
        self.main_layout.addSpacerItem(QtWidgets.QSpacerItem(10, 10, QtWidgets.QSizePolicy.Expanding, QtWidgets.QSizePolicy.Expanding))

    def _setupSocketConnections(self):
        self._comboBox.currentIndexChanged.connect(self._widgetUpdated)

    def _silentUpdateSelf(self):
            self._comboBox.currentIndexChanged.disconnect(self._widgetUpdated)
            self._comboBox.setCurrentIndex(self._value)
            self._comboBox.currentIndexChanged.connect(self._widgetUpdated)

    def _updateWidgetValues(self):
        self._silentUpdateSelf
        super(EnumAttributeWidget, self)._updateWidgetValues()

    def _widgetUpdated(self):
        self._value = self._comboBox.currentIndex()
        self._onSetAttr()
        super(EnumAttributeWidget, self)._widgetUpdated()

##  @brief Float Attibute Class Has a Label of the attribute Name, QDoublSpinBox, 
#   and QSlider setup with logic to sync it up with the QDoublSpinBox
#
class FloatNumericSimpleAttributeWidget(BaseAttributeWidget):

    IS_SIMPLE = True
    VALID_ATTR_TYPES = set(['doubleLinear','double','float','time','doubleAngle'])

    def __init__(self, parent=None, node=None, attribute=None, attributeType=None, **kwargs):
        super(FloatNumericSimpleAttributeWidget, self).__init__(
                                                                parent=parent, 
                                                                node=node, 
                                                                attribute=attribute, 
                                                                attributeType=attributeType, 
                                                                **kwargs
                                                                )

    def _getAttributeInformation(self):
        _attrData = dict(K_FLOAT_ATTR_DEFAULTS)
        if not cmds.objExists(str(self.plugString)):
            return _attrData

        _tempValue = cmds.getAttr(self.plugString)
        if _tempValue:
            _attrData['value'] = _tempValue

        if cmds.attributeQuery(self.attribute, node=self.node, minExists=True):
            _attrData['minimum'] = cmds.attributeQuery(self.attribute, node=self.node, minimum=True)[0]

        if cmds.attributeQuery(self.attribute, node=self.node, maxExists=True):
            _attrData['maximum'] = cmds.attributeQuery(self.attribute, node=self.node, maximum=True)[0]

        ##NOTE: Use this to limit the slider ranges
        if cmds.attributeQuery(self.attribute, node=self.node, softRangeExists=True):
            _attrData['softRange'] = cmds.attributeQuery(self.attribute, node=self.node, softRange=True)

        return _attrData

    def _buildWidget(self, **kwargs):

        _val    =   self._attributeDefaults['value']
        self._value = _val
        _min    =   self._attributeDefaults.get('minimum', None)
        _max    =   self._attributeDefaults.get('maximum', None)

        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        self.main_layout.setContentsMargins(QtCore.QMargins(0,0,0,0))
        self.setLayout(self.main_layout)

        ##  NOTE:   Need a Qlabel
        if not kwargs.get('noLabel', False):
            _useName = str(self._attribute).capitalize()
            if self._displayName:
                _useName=self._displayName
            self._label = QtWidgets.QLabel(_useName)
            self._label.setScaledContents(False)
            self._label.setMinimumWidth(125)
            self._label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
            self.main_layout.addWidget(self._label)

        ##  NOTE:   Need a QSpinBox
        self._spinBox = CustomQDoubleSpinBox(self)
        self._spinBox.setMinimumWidth(75)
        self._spinBox.setValue(_val)
        self._spinBox.setMinimum(_min)
        self._spinBox.setMaximum(_max)
        self._spinBox.setDecimals(3)
        self._spinBox.ButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self._spinBox.setSingleStep(self._customIncrement)
        self.main_layout.addWidget(self._spinBox)

    def _setupSocketConnections(self):
        ##  NOTE:   Create the commands to link the slider and double spinbox values
        self._spinBox.valueChanged.connect(self._spinBoxUpdated)

    def _spinBoxUpdated(self, val):
        self._value = val
        self._widgetUpdated()

    def _silentSpinBoxUpdate(self, val):
        self._spinBox.valueChanged.disconnect(self._spinBoxUpdated)
        self._spinBox.setValue(val)
        self._spinBox.valueChanged.connect(self._spinBoxUpdated)

    def _updateWidgetValues(self):
        if self._value != self._spinBox.value():
            self._silentSpinBoxUpdate(self._value)
        super(FloatNumericSimpleAttributeWidget, self)._updateWidgetValues()

    def _widgetUpdated(self):
        self._onSetAttr()
        super(FloatNumericSimpleAttributeWidget, self)._widgetUpdated()

##  @brief Float Attibute Class Has a Label of the attribute Name, QDoublSpinBox, 
#   and QSlider setup with logic to sync it up with the QDoublSpinBox
#
class FloatNumericAttributeWidget(FloatNumericSimpleAttributeWidget, BaseAttributeWidget):

    IS_SIMPLE = False

    def __init__(self, parent=None, node=None, attribute=None, attributeType=None, **kwargs):
        super(FloatNumericAttributeWidget, self).__init__(
                                                        parent=parent, 
                                                        node=node, 
                                                        attribute=attribute, 
                                                        attributeType=attributeType, 
                                                        **kwargs
                                                        )

    def _buildWidget(self, **kwargs):
        super(FloatNumericAttributeWidget, self)._buildWidget(**kwargs)

        _val    =   self._attributeDefaults['value']
        _range  =   [
                    (self._attributeDefaults['minimum'] * float(K_FLOAT_WIDGET_FACTOR)), 
                    (self._attributeDefaults['maximum'] * float(K_FLOAT_WIDGET_FACTOR))
                    ]

        ##  NOTE:   Need a Float Slider
        self._slider = CustomQSlider(self)
        self._slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self._slider.setValue(_val)
        self._slider.setMinimum(_range[0])
        self._slider.setMaximum(_range[1])
        self._slider.setTickInterval(self._customIncrement)
        self._slider.setSingleStep(self._customIncrement)
        self._slider.setOrientation(QtCore.Qt.Horizontal)
        self.main_layout.addWidget(self._slider)

    def _setupSocketConnections(self):
        super(FloatNumericAttributeWidget, self)._setupSocketConnections()
        self._slider.valueChanged.connect(self._sliderUpdated)

        ##  NOTE:   Need to set values to make sure connection update is in sync
        self._spinBox.setValue((self._attributeDefaults['value'] + 1))
        self._spinBox.setValue(self._attributeDefaults['value'])

    def _spinBoxUpdated(self, val):
        self._silentSliderUpdate(val)
        super(FloatNumericAttributeWidget, self)._spinBoxUpdated(val)

    def _sliderUpdated(self, val):
        #NOTE: Need to update the slider along with any connections, but not trigger any connections
        self._value = val / float(K_FLOAT_WIDGET_FACTOR)
        self._silentSpinBoxUpdate(self._value)
        self._widgetUpdated()

    def _silentSliderUpdate(self, val):
        #NOTE: Need to update the spinBox along with any connections, but not trigger any connections
        self._slider.valueChanged.disconnect(self._sliderUpdated)
        self._slider.setValue(val * float(K_FLOAT_WIDGET_FACTOR))
        self._slider.valueChanged.connect(self._sliderUpdated)

    def _updateWidgetValues(self):
        super(FloatNumericAttributeWidget, self)._updateWidgetValues()
        if self._value != (self._slider.value() / float(K_FLOAT_WIDGET_FACTOR)):
            self._silentSliderUpdate(self._value * float(K_FLOAT_WIDGET_FACTOR))

##  @brief Integer Attibute Class Has an optional Label, and a QSpinBox that controls Integer Attributes 
#
class IntegerNumericSimpleAttributeWidget(BaseAttributeWidget):

    IS_SIMPLE = True
    VALID_ATTR_TYPES = set(['long', 'short', 'byte'])

    def __init__(self, parent=None, node=None, attribute=None, attributeType=None, **kwargs):
        super(IntegerNumericSimpleAttributeWidget, self).__init__(
                                                            parent=parent, 
                                                            node=node, 
                                                            attribute=attribute, 
                                                            attributeType=attributeType, 
                                                            **kwargs
                                                            )

    def _getAttributeInformation(self):
        _attrData = dict(K_INTEGER_ATTR_DEFAULTS)
        if not cmds.objExists(str(self.plugString)):
            return _attrData

        _tempValue = cmds.getAttr(self.plugString)
        if _tempValue:
            _attrData['value'] = _tempValue

        if cmds.attributeQuery(self.attribute, node=self.node, minExists=True):
            _attrData['minimum'] = cmds.attributeQuery(self.attribute, node=self.node, minimum=True)[0]

        if cmds.attributeQuery(self.attribute, node=self.node, maxExists=True):
            _attrData['maximum'] = cmds.attributeQuery(self.attribute, node=self.node, maximum=True)[0]

        ##NOTE: Use this to limit the slider ranges
        if cmds.attributeQuery(self.attribute, node=self.node, softRangeExists=True):
            _attrData['softRange'] = cmds.attributeQuery(self.attribute, node=self.node, softRange=True)

        return _attrData

    def _buildWidget(self, **kwargs):
        _val = int(self._attributeDefaults['value'])
        self._value = _val
        _min = int(self._attributeDefaults['softRange'][0]) #int(self._attributeDefaults['minimum'])
        _max = int(self._attributeDefaults['softRange'][1]) #int(self._attributeDefaults['maximum'])
        _range = [int(self._attributeDefaults['softRange'][0]), int(self._attributeDefaults['softRange'][1])]


        self.setSizePolicy(QtWidgets.QSizePolicy.Preferred, QtWidgets.QSizePolicy.Fixed)
        self.main_layout = QtWidgets.QHBoxLayout()
        self.main_layout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        self.main_layout.setContentsMargins(QtCore.QMargins(0,0,0,0))

        self.setLayout(self.main_layout)

        if not kwargs.get('noLabel', False):
        #NOTE: Need a Qlabel
            _useName = str(self._attribute).capitalize()
            if self._displayName:
                _useName=self._displayName
            self._label = QtWidgets.QLabel(_useName)
            self._label.setScaledContents(False)
            self._label.setMinimumWidth(125)
            self._label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)
            self.main_layout.addWidget(self._label)

        #NOTE: Need a SpinBox
        self._spinBox = CustomQSpinBox(self)
        self._spinBox.setMinimumWidth(75)
        self._spinBox.setValue(_val)
        self._spinBox.setMinimum(_min)
        self._spinBox.setMaximum(_max)
        self._spinBox.ButtonSymbols(QtWidgets.QAbstractSpinBox.PlusMinus)
        self._spinBox.setSingleStep(int(K_INTEGER_WIDGET_STEP_INCREMENT))
        self._spinBox.setValue(_val)

        self.main_layout.addWidget(self._spinBox)

    def _setupSocketConnections(self):
        self._spinBox.valueChanged.connect(self._spinBoxUpdated)

    def _spinBoxUpdated(self, val):
        #NOTE: Need to update the slider along with any connections, but not trigger any connections
        self._value = val
        self._widgetUpdated()
        
    def _silentSpinBoxUpdate(self, val):
        self._spinBox.valueChanged.disconnect(self._spinBoxUpdated)
        self._spinBox.setValue(val)
        self._spinBox.valueChanged.connect(self._spinBoxUpdated)

    def _updateWidgetValues(self):
        if self._value != self._spinBox.value():
            self._silentSpinBoxUpdate(self._value)
        super(IntegerNumericSimpleAttributeWidget, self)._updateWidgetValues()

    def _widgetUpdated(self):
        self._onSetAttr()
        super(IntegerNumericSimpleAttributeWidget, self)._widgetUpdated()

##  @brief Integer Attibute Class Extension of "IntegerNumericSimpleAttributeWidget" with additional QSlider
#
class IntegerNumericAttributeWidget(IntegerNumericSimpleAttributeWidget, BaseAttributeWidget):

    IS_SIMPLE = False

    def __init__(self, parent=None, node=None, attribute=None, attributeType=None, **kwargs):
        super(IntegerNumericAttributeWidget, self).__init__(
                                                            parent=parent, 
                                                            node=node, 
                                                            attribute=attribute, 
                                                            attributeType=attributeType, 
                                                            **kwargs
                                                            )

    def _buildWidget(self, **kwargs):
        super(IntegerNumericAttributeWidget, self)._buildWidget(**kwargs)

        _val = int(self._attributeDefaults['value'])
        _min = int(self._attributeDefaults['softRange'][0]) #int(self._attributeDefaults['minimum'])
        _max = int(self._attributeDefaults['softRange'][1]) #int(self._attributeDefaults['maximum'])

        #NOTE: Need a Splider
        self._slider = CustomQSlider(self)
        self._slider.setTickPosition(QtWidgets.QSlider.TicksBothSides)
        self._slider.setTickInterval(int(K_INTEGER_WIDGET_STEP_INCREMENT))
        self._slider.setValue(_val)
        self._slider.setMinimum(_min)
        self._slider.setMaximum(_max)
        self._slider.setSingleStep(int(K_INTEGER_WIDGET_STEP_INCREMENT))
        
        #NOTE: the slider should expand indefinently to the right
        self._slider.setOrientation(QtCore.Qt.Horizontal)

        self.main_layout.addWidget(self._slider)

    def _setupSocketConnections(self):
        super(IntegerNumericAttributeWidget, self)._setupSocketConnections()
        self._slider.valueChanged.connect(self._sliderUpdated)

    def _spinBoxUpdated(self, val):
        self._silentSliderUpdate(val)
        super(IntegerNumericAttributeWidget, self)._spinBoxUpdated(val)

    def _sliderUpdated(self, val):
        self._silentSpinBoxUpdate(val)
        self._value = val
        self._widgetUpdated()

    def _silentSliderUpdate(self, val):
        self._slider.valueChanged.disconnect(self._sliderUpdated)
        self._slider.setValue(val)
        self._slider.valueChanged.connect(self._sliderUpdated)

    def _updateWidgetValues(self):
        super(IntegerNumericAttributeWidget, self)._updateWidgetValues()
        if self._value != self._slider.value():
            self._silentSliderUpdate(self._value)

##  @brief Boolean Attibute Class has a QCheckBox with its label set to the attribute given, 
#   and a spacer to keep the checkbox pushed to the right side
#
class BoolAttributeWidget(BaseAttributeWidget):

    VALID_ATTR_TYPES = set(['bool'])

    def __init__(self, parent=None, node=None, attribute=None, attributeType=None, **kwargs):
        super(BoolAttributeWidget, self).__init__(
                                                parent=parent, 
                                                node=node, 
                                                attribute=attribute, 
                                                attributeType=attributeType, 
                                                **kwargs
                                                )
       
    def _getAttributeInformation(self):
        _attrData = {'value':False}
        if not cmds.objExists(str(self.plugString)):
            return _attrData

        _attrData['value'] = cmds.getAttr(self.plugString)
        return _attrData
        
    def _buildWidget(self, **kwargs):
        self.main_layout = QtWidgets.QFormLayout()
        self.main_layout.setAlignment(QtCore.Qt.AlignCenter | QtCore.Qt.AlignCenter)
        self.setLayout(self.main_layout)

        #NOTE: Create and add a CheckBox
        _useName = str(self._attribute).capitalize()
        if self._displayName:
            _useName=self._displayName
        self._label = QtWidgets.QLabel(_useName)
        self._label.setScaledContents(False)
        self._label.setMinimumWidth(125)
        self._label.setAlignment(QtCore.Qt.AlignVCenter | QtCore.Qt.AlignRight)

        self._checkBox = QtWidgets.QCheckBox()
        self._value = self._attributeDefaults['value']
        self.main_layout.addRow(_useName, self._checkBox)

    def _setupSocketConnections(self):
        self._checkBox.stateChanged.connect(self._widgetUpdated)
        self._checkBox.setChecked(self._value)
        
    def _updateWidgetValues(self):
        self._checkBox.setChecked(self._value)        
        super(BoolAttributeWidget, self)._updateWidgetValues()

    def _widgetUpdated(self):
        _val = self._checkBox.isChecked()
        self._value = _val
        self._onSetAttr()
        super(BoolAttributeWidget, self)._widgetUpdated()


##  @Breif: Method for creating Attribute Widgets based on attributeTypes, and plug information
#
def AttributeWidgetFactory(parent=None, node=None, attribute=None, attributeType=None, **kwargs):
    if not attributeType:
        raise TypeError('You must at least pass an attributeType into the Factory')

    _createdWidget=None

    _allWidgetTypes = BaseAttributeWidget.__subclasses__()
    for _attrClass in _allWidgetTypes:
        if hasattr(_attrClass, 'IS_SIMPLE'):
            _simpleValue = getattr(_attrClass, 'IS_SIMPLE')
            if _simpleValue and not kwargs.get('noLabel', False):
                _logger.info('Skipping, desire Non Simple Class: {}'.format(_attrClass))
                continue               

        if attributeType in _attrClass.VALID_ATTR_TYPES:
            _createdWidget = _attrClass(
                                        parent=parent, 
                                        node=node, 
                                        attribute=attribute,  
                                        attributeType=str(attributeType), 
                                        value=kwargs.get('value', 0),
                                        displayName=kwargs.get('displayName', ''),
                                        noLabel=kwargs.get('noLabel', False)
                                        )
            break                                        
    return _createdWidget


