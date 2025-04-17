# My Maya Plugins

## Limb Rigger

<img src="./assets/LimbRigger.png" width=200>

[Github](https://github.com/FreezyDev07/MayaPlugins2025Spring)

this plugin rigs any 3 joint limb with ik, fk and ikfk blend.

* support auto joint finding
* controller size control
* controller color control

# Proxy Generator

Uses vertices in proximity to joints to duplicate and split the mesh into separate segments.

Finds specific vertices and joints too see which have the most influence over the mesh/skin, and splits them into duplicate mesh pieces, labeled by the joint names.
It is also able to create a dictionary of all the joints and vertices to sort them properly and find the correct data to create the duplicate meshes.

MayaUtils holds defintions for functions including 
* IsMesh, IsJoint, IsSkin
* GetLowerStream, GetUpperStream
* GetAllConnectionsIn

These reduce the load of the original file and help it find specific parts of the mesh and skeleton.
It also holds the classes and functions to create the Maya plugin window
