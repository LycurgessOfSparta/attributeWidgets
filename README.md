# attributeWidgets
 Maya Pyside Attribute Widgets for UI use

    Pyside widgets for attribute controls within Maya. 
        ---- Each Widget has the ability to connect to a plug and be driven, or drive that attributes value simply "setLiveMode" to True
        ---- The widgets all emit a "valueChanged" signal when there value is updated, via user manipulation
        ---- You can steal or set the attributes current data via the "stealMyData" or "pushInData" functions
        ---- SpinBox widgets attempt to set their limits based on the soft ranges of the given plugs
        ---- Enum or option type attributes should give all there options as available members of a combo box

        @note   Some of this is taken and modified from the Maya devKit connectAttr.py