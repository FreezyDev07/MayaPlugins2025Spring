from PySide2.QtWidgets import QColorDialog, QHBoxLayout, QLabel, QLineEdit, QMainWindow, QMessageBox, QPushButton, QSlider, QVBoxLayout, QWidget # imports all ui we use
from PySide2.QtCore import Qt, Signal # used to configure the window
from maya.OpenMaya import MVector
import maya.OpenMayaUI as omui # imports maya ui
import shiboken2 # translates Qt functions to python
import maya.mel as mel
import maya.cmds as mc # imports maya command menu so we can do maya commands thru python
from PySide2.QtGui import QColor

def GetMayaMainWindow():  # gets main window from maya
    mainWindow = omui.MQtUtil.mainWindow()
    return shiboken2.wrapInstance(int(mainWindow), QMainWindow)

def DeleteWidgetWithName(name): # when window is opened again, it closes the first one and opens another
    for widget in GetMayaMainWindow().findChildren(QWidget, name):
        widget.deleteLater()

class MayaWindow(QWidget): # creates maya window
    def __init__(self): # constructor for maya widget parts
        super().__init__(parent = GetMayaMainWindow()) 
        DeleteWidgetWithName(self.GetWidgetUniqueName())
        self.setWindowFlags(Qt.WindowType.Window) 
        self.setObjectName(self.GetWidgetUniqueName())

    def GetWidgetUniqueName(self): # gives widget ID for maya script editor
        return "iytfvbjytfdcvhj" 
    
class LimbRigger: # LimbRigger tool
    def __init__(self): # constructor for joint parts
        self.root = "" 
        self.mid = "" 
        self.end = "" 
        self.controllerSize = 15 
        self.controllerColor = [0,0,0]

    def FindJointsBasedOnSelection(self): # finds other joints connected to the root joint
        try:
            self.root = mc.ls(sl=True, type="joint")[0] 
            self.mid = mc.listRelatives(self.root, c = True, type="joint")[0] 
            self.end = mc.listRelatives(self.mid, c = True, type="joint")[0] 
        except Exception as e: # error 
            raise Exception("Wrong Selection, please select the first Joint of the limb!") 


    def CreateFKControllerForJoint(self, jntName): # creates fkik controllers
        ctrlName = "ac_l_fk_" + jntName 
        ctrlGrpName = ctrlName + "_grp" 
        mc.circle(name = ctrlName, radius = self.controllerSize, normal = (1,0,0)) 
        mc.group(ctrlName, n=ctrlGrpName)
        mc.matchTransform(ctrlGrpName, jntName) 
        mc.orientConstraint(ctrlName, jntName) 
        return ctrlName, ctrlGrpName 
    
    def CreateBoxController(self, name):
        mel.eval(f"curve -n {name} -d 1 -p 0.5 0.5 0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p 0.5 0.5 0.5 -p 0.5 -0.5 0.5 -p 0.5 -0.5 -0.5 -p 0.5 0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 -0.5 -0.5 -p 0.5 -0.5 -0.5 -p 0.5 -0.5 0.5 -p -0.5 -0.5 0.5 -p -0.5 -0.5 -0.5 -p -0.5 0.5 -0.5 -p -0.5 0.5 0.5 -p -0.5 -0.5 0.5 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 -k 13 -k 14 -k 15 -k 16 ;")
        mc.scale(self.controllerSize, self.controllerSize, self.controllerSize, name)
        mc.makeIdentity(name, apply=True) # freeze transformation
        grpName = name + "_grp"
        mc.group(name, n = grpName)
        return name, grpName
    
    def CreatePlusController(self, name):
        mel.eval(f"curve - n {name} -d 1 -p 0 0 0 -p 0 100 0 -p -100 100 0 -p -100 0 0 -p -200 0 0 -p -200 -100 0 -p -100 -100 0 -p -100 -200 0 -p 0 -200 0 -p 0 -100 0 -p 100 -100 0 -p 100 0 0 -p 0 0 0 -k 0 -k 1 -k 2 -k 3 -k 4 -k 5 -k 6 -k 7 -k 8 -k 9 -k 10 -k 11 -k 12 ;")
        grpName = name + "_grp"
        mc.group(name, n = grpName)
        return name, grpName
    
    
    def GetObjectLocation(self, objectName):
        x, y, z = mc.xform(objectName, q=True, ws=True, t=True) # queries the translation of the object in world space
        return MVector(x, y, z)
    
    def PrintMVector(self, vector):
        print(f"<{vector.x}, {vector.y}, {vector.z}>")

    def RigLimb(self): # creates controllers and parents them to joints
        rootCtrl, rootCtrlGrp = self.CreateFKControllerForJoint(self.root)
        midCtrl, midCtrlGrp = self.CreateFKControllerForJoint(self.mid)
        endCtrl, endtCtrlGrp = self.CreateFKControllerForJoint(self.end)

        mc.parent(midCtrlGrp, rootCtrl)
        mc.parent(endtCtrlGrp, midCtrl)

        ikEndCtrl = "ac_ik_" + self.end
        ikEndCtrl, ikEndCtrlGrp = self.CreateBoxController(ikEndCtrl)
        mc.matchTransform(ikEndCtrlGrp, self.end)
        endOrientConstraint = mc.orientConstraint(ikEndCtrl, self.end)[0]

        rootJntLoc = self.GetObjectLocation(self.root)
        self.PrintMVector(rootJntLoc)

        ikHandleName = "ikHandle_" + self.end
        mc.ikHandle(n=ikHandleName, sol="ikRPsolver", sj=self.root, ee=self.end)

        poleVectorLocationVals = mc.getAttr(ikHandleName + ".poleVector")[0]
        poleVector = MVector(poleVectorLocationVals[0], poleVectorLocationVals[1], poleVectorLocationVals[2])
        poleVector.normalize()

        endJntLoc = self.GetObjectLocation(self.end)
        rootToEndVector = endJntLoc - rootJntLoc

        poleVectorCtrlLoc = rootJntLoc + rootToEndVector / 2 + poleVector * rootToEndVector.length()
        poleVectorCtrl = "ac_ik_" + self.mid
        mc.spaceLocator(n=poleVectorCtrl)
        poleVectorCtrlGrp = poleVectorCtrl + "_grp"
        mc.group(poleVectorCtrl, n=poleVectorCtrlGrp)
        mc.setAttr(poleVectorCtrlGrp+".t", poleVectorCtrlLoc.x, poleVectorCtrlLoc.y, poleVectorCtrlLoc.z, typ="double3")

        mc.poleVectorConstraint(poleVectorCtrl, ikHandleName)

        ikfkBlendCtrl = "ac_ikfk_blend_" + self.root
        ikfkBlendCtrl, ikfkBlendCtrlGrp = self.CreatePlusController(ikfkBlendCtrl)
        mc.setAttr(ikfkBlendCtrlGrp+".t", rootJntLoc.x*-10, rootJntLoc.y, rootJntLoc.z, typ="double3")

        ikfkBlendAttrName = "ikfkBlend"
        mc.addAttr(ikfkBlendCtrl, ln=ikfkBlendAttrName, min = 0, max = 1, k=True)
        ikfkBlendAttr = ikfkBlendCtrl + "." + ikfkBlendAttrName

        mc.expression(s=f"{ikHandleName}.ikBlend={ikfkBlendAttr}")
        mc.expression(s=f"{ikEndCtrlGrp}.v={poleVectorCtrlGrp}.v={ikfkBlendAttr}")
        mc.expression(s=f"{rootCtrlGrp}.v=1-{ikfkBlendAttr}")
        mc.expression(s=f"{endOrientConstraint}.{endCtrl}W0 = 1-{ikfkBlendAttr}")
        mc.expression(s=f"{endOrientConstraint}.{ikEndCtrl}W1 = {ikfkBlendAttr}")

        topGrpName = f"{self.root}_rig_grp"
        mc.group([rootCtrlGrp, ikEndCtrlGrp, poleVectorCtrlGrp, ikfkBlendCtrlGrp], n=topGrpName)
        mc.parent(ikHandleName, ikEndCtrl)

        mc.setAttr(topGrpName+".overrideEnabled", 1)
        mc.setAttr(topGrpName+".overrideRGBColors", 1)
        mc.setAttr(topGrpName+".overrideColorRGB", self.controllerColor[0], self.controllerColor[1], self.controllerColor[2], type="double3")

class ColorPicker(QWidget):
    colorChanged = Signal(QColor)
    def __init__(self):
        super().__init__()
        self.masterLayout = QVBoxLayout()
        self.color = QColor()
        self.setLayout(self.masterLayout)
        self.pickColorBtn = QPushButton()
        self.pickColorBtn.setStyleSheet(f"background-color:black")
        self.pickColorBtn.clicked.connect(self.ColorPickerBtnClicked)
        self.masterLayout.addWidget(self.pickColorBtn)
 
    def ColorPickerBtnClicked(self):
        self.color = QColorDialog.getColor()
        self.pickColorBtn.setStyleSheet(f"background-color:{self.color.name()}")
        self.colorChanged.emit(self.color)

class LimbRiggerWidget(MayaWindow): # LimbRigger maya widget menu
    def __init__(self): # constructor for rigger widget parts
        super().__init__() 
        self.rigger = LimbRigger() # gives function to rigger variable
        self.setWindowTitle("Limb Rigger v1.0.0")

        self.masterLayout = QVBoxLayout() # gets layout from Qt
        self.setLayout(self.masterLayout) # gives new layout to setLayout function

        toolTipLabel = QLabel("Select the first joint of the limb, and press auto find button")
        self.masterLayout.addWidget(toolTipLabel) # creates tooltip

        self.jntsListLineEdit = QLineEdit() # makes space for joint list
        self.masterLayout.addWidget(self.jntsListLineEdit) # shows the selected joints
        self.jntsListLineEdit.setEnabled(False) # makes it so you can't interact with the list

        autoFindJntBtn = QPushButton("Auto Find") # creates and labels autoFind button
        autoFindJntBtn.clicked.connect(self.AutoFindJntBtnClicked) # when button is clicked it does the action connected to it
        self.masterLayout.addWidget(autoFindJntBtn) # adds button to window

        ctrlSizeSlider = QSlider()
        ctrlSizeSlider.setOrientation(Qt.Horizontal)
        ctrlSizeSlider.setRange(1, 30)
        ctrlSizeSlider.setValue(self.rigger.controllerSize)
        self.ctrlSizeLabel = QLabel(f"{self.rigger.controllerSize}")
        ctrlSizeSlider.valueChanged.connect(self.CtrlSizeSliderChanged)

        ctrlSizeLayout = QHBoxLayout()
        ctrlSizeLayout.addWidget(ctrlSizeSlider)
        ctrlSizeLayout.addWidget(self.ctrlSizeLabel)
        self.masterLayout.addLayout(ctrlSizeLayout)

        colorPicker = ColorPicker()
        colorPicker.colorChanged.connect(self.ColorPickerChanged)
        self.masterLayout.addWidget(colorPicker)

        rigLimbBtn = QPushButton("Rig Limb") # creates and labels rigLimb button
        rigLimbBtn.clicked.connect(lambda : self.rigger.RigLimb()) # when button is clicked it does the action connected to it
        self.masterLayout.addWidget(rigLimbBtn) # adds button to window

    def ColorPickerChanged(self, newColor: QColor):
        self.rigger.controllerColor[0] = newColor.redF()
        self.rigger.controllerColor[0] = newColor.greenF()
        self.rigger.controllerColor[0] = newColor.blueF()
        
    def CtrlSizeSliderChanged(self, newValue):
        self.ctrlSizeLabel.setText(f"{newValue}")
        self.rigger.controllerSize = newValue

    def AutoFindJntBtnClicked(self): # action for autoFind button
        try:
            self.rigger.FindJointsBasedOnSelection()
            self.jntsListLineEdit.setText(f"{self.rigger.root},{self.rigger.mid},{self.rigger.end}")
        except Exception as e: # error
            QMessageBox.critical(self, "Error", f"{e}") 


limbRiggerWidget = LimbRiggerWidget() # gives attributes to function
limbRiggerWidget.show() # gives function to window

GetMayaMainWindow() # calls function to open window