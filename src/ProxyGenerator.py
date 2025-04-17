import importlib
import MayaUtils
importlib.reload(MayaUtils)

from MayaUtils import *
from PySide2.QtWidgets import QLabel, QPushButton, QVBoxLayout
import maya.cmds as mc

class ProxyGenerator:
    def __init__(self):
        self.skin = ""
        self.model = ""
        self.jnts = []

    def BuildProxyForSelectedMesh(self):
        model = mc.ls(sl=True)[0]
        if not IsMesh(model):
            print(f"{model} is not a mesh!")
            return
        
        self.model = model
        print(f"found model {self.model}")
        modelShape = mc.listRelatives(self.model,s=True)[0]
        skin = GetAllConnectionsIn(modelShape, GetUpperStream, IsSkin)
        if not skin:
            print(f"{self.model} is not bound!")
            return
        
        jnts = GetAllConnectionsIn(modelShape, GetUpperStream, IsJoint)
        if not jnts:
            print(f"{self.model} is not bound with any joint!")
            return
        
        self.skin = skin
        self.jnts = jnts
        print(f"found model: {self.model} with ski:n {self.skin} and joints: {self.jnts}")

        jntVertDict = self.GenerateJntVertsDict()
        chunks = []
        ctrls = []
        for jnt, verts in jntVertDict.items():
            newChunk = self.CreateProxyModelForJntAndVerts(jnt, verts)

    
    def CreateProxyModelForJntAndVerts(self, jnt, verts):
        if not verts:
            return None
        
        faces = mc.polyListComponentConversion(verts, fromVertex=True, toFace=True)
        faces = mc.ls(faces, fl=True)

        faceNames = set()
        for face in faces:
            faceNames.add(face.replace(self.model, ""))

        dup = mc.duplicate(self.model)[0]

        allDupFaces = mc.ls(f"{dup}.f[*]", fl=True)
        facesToDelete = []
        for dupFace in allDupFaces:
            if dupFace.replace(dup, "") not in faceNames:
                facesToDelete.append(dupFace)

        mc.delete(facesToDelete)

        dupName = self.model + "_" + jnt + "_proxy"
        mc.rename(dup, dupName)
        return dupName


    def GenerateJntVertsDict(self):
        dict = {}
        for jnt in self.jnts:
            dict[jnt] = []
        
        verts= mc.ls(f"{self.model}.vtx[*]", fl=True)
        for vert in verts:
            owningJnt = self.GetJntWithMaxInfluence(vert, self.skin)
            dict[owningJnt].append(vert)

        return dict


    def GetJntWithMaxInfluence(self, vert, skin):
        weights = mc.skinPercent(skin, vert, q=True, v=True)
        jnts= mc.skinPercent(skin, vert, q=True, t=None)

        maxWeightIndex = 0
        maxWeight = weights[0]
        for i in range(1, len(weights)):
            if weights[i] > maxWeight:
                maxWeight = weights[i]
                maxWeightIndex = i

        return jnts[maxWeightIndex]


class ProxyGeneratorWidget(MayaWindow):
    def __init__(self):
        super().__init__()
        self.generator = ProxyGenerator()
        self.masterLayout = QVBoxLayout()
        self.setLayout(self.masterLayout)

        self.masterLayout.addWidget(QLabel("Please selected the rigged model, and press the build button"))
        buildBtn = QPushButton("Build")
        self.masterLayout.addWidget(buildBtn)
        buildBtn.clicked.connect(self.generator.BuildProxyForSelectedMesh)
        self.setWindowTitle("Proxy Generator")

    def GetWidgetUniqueName(self):
        return "ProxyGeneratorJS4152025213"
    
ProxyGeneratorWidget().show()
