import os
from MayaUtils import *
from PySide2.QtCore import Signal
from PySide2.QtGui import QIntValidator, QRegExpValidator
from PySide2.QtWidgets import QCheckBox, QFileDialog, QHBoxLayout, QLabel, QLineEdit, QListWidget, QMessageBox, QPushButton, QVBoxLayout
import maya.cmds as mc

def TryAction(actionFunc):
    def wrapper(*args, **kwargs):
        try:
            actionFunc(*args, **kwargs)
        except Exception as e:
            QMessageBox().critical(None, "error!", f"{e}")

    return wrapper

class AnimClip:
    def __init__(self):
        self.subfix = ""
        self.frameMin = mc.playbackOptions(q=True, min=True)
        self.frameMax = mc.playbackOptions(q=True, max=True)
        self.shouldExport = True

class MayaToUE:
    def __init__(self):
        self.rootJnt = ""
        self.models = set()
        self.animations : list[AnimClip] = []
        self.fileName = ""
        self.saveDir = ""

    def SendToUnreal(self):
        # save the files:
        allJnts = []
        allJnts.append(self.rootJnt)
        children = mc.listRelatives(self.rootJnt, c=True, ad=True, type="joint")
        if children:
            allJnts.extend(children)

        allMeshs = self.models
        allObjectToExport = allJnts + list(allMeshs)

        mc.select(allObjectToExport, r=True)
        skeletalMeshExportPath = self.GetSkeletalMeshSavePath()

        mc.FBXResetExport() # resets all the settings
        mc.FBXExportSmoothGroups("-v", True)
        mc.FBXExportInputConnections("-v", False)

        # -f means the file name, -s means export selected, -ea means export animation
        mc.FBXExport('-f', skeletalMeshExportPath, '-s', True, '-ea', False)

        if self.animations:
            mc.FBXExportBakeComplexAnimation('-v', True)
            os.makedirs(os.path.join(self.saveDir, "animations"), exist_ok=True)

            for animClip in self.animations:
                if not animClip.shouldExport:
                    continue

            animExportPath = self.GetSavePathForAnimClip(animClip)

            startFrame = animClip.frameMin
            endFrame = animClip.frameMax

            mc.FBXExportBakeComplexStart('-v', startFrame)
            mc.FBXExportBakeComplexend('-v', endFrame)
            mc.FBXExportBakeComplexStep('-v', 1)

            mc.playbackOptions(e=True, min=startFrame, max=endFrame)

            mc.FBXExport('-f', animExportPath, "-s", True, '-ea', True)


    def GetSkeletalMeshSavePath(self):
        savePath = os.path.join(self.saveDir, self.fileName + ".fbx")
        return os.path.normpath(savePath)
    
    def GetSavePathForAnimClip(self, animClip: AnimClip):
        savePath = os.path.join(self.saveDir, "animations", self.fileName + animClip.subfix + ".fbx")
        return os.path.normpath(savePath)

    def RemoveAnimClip(self, animClip: AnimClip):
        self.animations.remove(animClip)
        print(f"removed anim clip, now have: {len(self.animations)} left")

    def AddNewAnimClip(self):
        self.animations.append(AnimClip())
        print(f"added anim clip, now we have: {len(self.animations)} clips")
        return self.animations[-1]

    def AddSelectedMeshes(self):
        selection = mc.ls(sl=True)

        meshes = []
        if not selection:
            raise Exception("No mesh selected, please select all the meshes of your rig")
        
        meshes = []
        for sel in selection:
            if IsMesh(sel):
                meshes.append(sel)

        if len(meshes) == 0:
            raise Exception("No mesh selected, please select all the meshes of your rig")

        self.models = meshes


    def AddRootJoint(self):
        if not self.rootJnt:
            raise Exception("No root joint assigned, please set the root joint of your rig first")
        
        if mc.objExists(self.rootJnt):
            currentRootPos = mc.xform(self.rootJnt, q=True, ws=True, t=True)
            if currentRootPos[0] == 0 and currentRootPos[1] == 0 and currentRootPos[2] == 0:
                raise Exception("Current root joint is at origin already, no need to make a new one!")
            
        mc.select(cl=True)
        rootJntname = self.rootJnt + "_root"
        mc.joint(n=rootJntname)
        mc.parent(self.rootJnt, rootJntname)
        self.rootJnt = rootJntname


    def SetSelectedJointAsRoot(self):
        selection = mc.ls(sl=True, type="joint")
        if not selection:
            raise Exception("Wrong selection, please select the root joint of your rig!")
        
        self.rootJnt = selection[0]


class AnimClipWidget(QWidget):
    animClipRemoved = Signal(AnimClip)
    animClipSubFixChange = Signal(str)
    def __init__(self, animClip: AnimClip):
        super().__init__()
        self.animClip = animClip
        self.masterLayout = QHBoxLayout()
        self.setLayout(self.masterLayout)

        shouldExportCheckbox = QCheckBox()
        shouldExportCheckbox.setChecked(self.animClip.shouldExport)
        self.masterLayout.addWidget(shouldExportCheckbox)
        shouldExportCheckbox.toggled.connect(self.ShouldExportCheckboxToggled)

        subfixLabel = QLabel("Subfix: ")
        self.masterLayout.addWidget(subfixLabel)

        subfixLineEdit = QLineEdit()
        subfixLineEdit.setValidator(QRegExpValidator("[a-zA-z0-9_]+"))
        subfixLineEdit.setText(self.animClip.subfix)
        subfixLineEdit.textChanged.connect(self.SubfixTextChanged)
        self.masterLayout.addWidget(subfixLineEdit)

        minFrameLabel = QLabel("min: ")
        self.masterLayout.addWidget(minFrameLabel)
        minFrameLineEdit = QLineEdit()
        minFrameLineEdit.setValidator(QIntValidator())
        minFrameLineEdit.setText(str(int(self.animClip.frameMin)))
        minFrameLineEdit.textChanged.connect(self.MinFrameChanged)
        self.masterLayout.addWidget(minFrameLineEdit)

        maxFrameLabel = QLabel("max: ")
        self.masterLayout.addWidget(maxFrameLabel)
        maxFrameLineEdit = QLineEdit()
        maxFrameLineEdit.setValidator(QIntValidator())
        maxFrameLineEdit.setText(str(int(self.animClip.frameMax)))
        maxFrameLineEdit.textChanged.connect(self.MaxFrameChanged)
        self.masterLayout.addWidget(maxFrameLineEdit)

        setRangeBtn = QPushButton("[-]")
        setRangeBtn.clicked.connect(self.SetRangeBtnClicked)
        self.masterLayout.addWidget(setRangeBtn)

        deleteBtn = QPushButton("X")
        deleteBtn.clicked.connect(self.DeleteBtnClicked)
        self.masterLayout.addWidget(deleteBtn)

    def DeleteBtnClicked(self):
        self.animClipRemoved.emit(self.animClip)
        self.deleteLater()

    def SetRangeBtnClicked(self):
        mc.playbackOptions(e=True, min = self.animClip.frameMin, max = self.animClip.frameMax)
        mc.playbackOptions(e=True, ast = self.animClip.frameMin, aet = self.animClip.frameMax)

    def MinFrameChanged(self, newVal):
        self.animClip.frameMin = int(newVal)

    def MaxFrameChanged(self, newVal):
        self.animClip.frameMax = int(newVal)

    def SubfixTextChanged(self, newText):
        self.animClip.subfix = newText
        self.animClipSubFixChange.emit(newText)

    def ShouldExportCheckboxToggled(self):
        self.animClip.shouldExport = not self.animClip.shouldExport


class MayaToUEWidget(MayaWindow):
    def GetWidgetUniqueName(self):
        return "MayaToUEWidgetJS4172025408"
            
    def __init__(self):
        super().__init__()
        self.mayaToUE = MayaToUE()

        self.setWindowTitle("Maya to UE")
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.rootJntText = QLineEdit()
        self.rootJntText.setEnabled(False)
        self.masterLayout.addWidget(self.rootJntText)

        setSelectedAsRootJntBtn = QPushButton("set Root Joint")
        setSelectedAsRootJntBtn.clicked.connect(self.SetSelectedAsRootJntBtnClicked)
        self.masterLayout.addWidget(setSelectedAsRootJntBtn)

        addRootJntBtn = QPushButton("Add Root Joint")
        addRootJntBtn.clicked.connect(self.AddRootJntBtnClicked)
        self.masterLayout.addWidget(addRootJntBtn)

        self.meshList = QListWidget()
        self.masterLayout.addWidget(self.meshList)
        self.meshList.setMaximumHeight(100)

        addMeshesBtn = QPushButton("Add meshes")
        addMeshesBtn.clicked.connect(self.AddMeshesBtnClicked)
        self.masterLayout.addWidget(addMeshesBtn)

        addAnimEntryBtn = QPushButton("Add animation clip")
        addAnimEntryBtn.clicked.connect(self.AddAnimEntryBtnClicked)
        self.masterLayout.addWidget(addAnimEntryBtn)

        self.animClipEntryLayout = QVBoxLayout()
        self.masterLayout.addLayout(self.animClipEntryLayout)

        self.saveFileLayout = QHBoxLayout()
        self.masterLayout.addLayout(self.saveFileLayout)

        self.saveFileLayout.addWidget(QLabel("File Name: "))
        self.fileNameLineEdit = QLineEdit()
        self.fileNameLineEdit.setFixedWidth(80)
        self.fileNameLineEdit.setValidator(QRegExpValidator("\w+"))
        self.fileNameLineEdit.textChanged.connect(self.FileNameLineEditChanged)
        self.saveFileLayout.addWidget(self.fileNameLineEdit)

        self.saveFileLayout.addWidget(QLabel("Save Directory: "))
        self.saveDirLineEdit = QLineEdit()
        self.saveDirLineEdit.setEnabled(False)
        self.saveFileLayout.addWidget(self.saveDirLineEdit)

        self.pickDirBtn= QPushButton("...")
        self.pickDirBtn.clicked.connect(self.PickDirBtnClicked)
        self.saveFileLayout.addWidget(self.pickDirBtn)

        self.savePreviewLabel = QLabel("")
        self.masterLayout.addWidget(self.savePreviewLabel)

        sendToUEBtn = QPushButton("Send to Unreal")
        sendToUEBtn.clicked.connect(self.mayaToUE.SendToUnreal)
        self.masterLayout.addWidget(sendToUEBtn)

    def UpdateSavePreviewLabel(self):
        previewText = self.mayaToUE.GetSkeletalMeshSavePath()
        for animClip in self.mayaToUE.animations:
            animSavePath = self.mayaToUE.GetSavePathForAnimClip(animClip)
            previewText += "\n" + animSavePath

            self.savePreviewLabel.setText(previewText)

    def PickDirBtnClicked(self):
        pickedPath = QFileDialog().getExistingDirectory()
        self.saveDirLineEdit.setText(pickedPath)
        self.mayaToUE.saveDir = pickedPath
        self.UpdateSavePreviewLabel()

    def FileNameLineEditChanged(self, newVal):
        self.mayaToUE.fileName = newVal
        self.UpdateSavePreviewLabel()

    @TryAction
    def AddAnimEntryBtnClicked(self):
        newAnimClip = self.mayaToUE.AddNewAnimClip()
        newAnimClipWidget = AnimClipWidget(newAnimClip)
        newAnimClipWidget.animClipRemoved.connect(self.AnimationClipRemoved)
        newAnimClipWidget.animClipSubFixChange.connect(lambda *arg : self.UpdateSavePreviewLabel())
        self.animClipEntryLayout.addWidget(newAnimClipWidget)
        self.UpdateSavePreviewLabel()

    @TryAction
    def AnimationClipRemoved(self, animClip: AnimClip):
        self.mayaToUE.RemoveAnimClip(animClip)
        self.UpdateSavePreviewLabel()

    @TryAction
    def AddMeshesBtnClicked(self):
        self.mayaToUE.AddSelectedMeshes()
        self.meshList.clear()
        self.meshList.addItems(self.mayaToUE.models)
    

    @TryAction
    def AddRootJntBtnClicked(self):
        self.mayaToUE.AddRootJoint()
        self.rootJntText.setText(self.mayaToUE.rootJnt)

    @TryAction
    def SetSelectedAsRootJntBtnClicked(self):
        self.mayaToUE.SetSelectedJointAsRoot()
        self.rootJntText.setText(self.mayaToUE.rootJnt)


MayaToUEWidget().show()
