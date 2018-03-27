## MMK Driving Simulator


1. Export an arbitrary chosen area from [OpenStreetMap](https://www.openstreetmap.org) as OpenStreetMap XML Data (ordinary .osm file) named *map.osm*.

2. Run *osmsanitizer.py* located in the CityEngine project in *scripts* folder using ```python3``` by specifying the path to the downloaded *map.osm* file. This will output a sanitized version of the original map which includes only drivable roads and buildings, named *map-sanitized.osm*.

	```
	python3 osmsanitizer.py map.osm
	```
3. Create a SUMO network simulation using ```netconvert``` and specify as osm input *map-sanitized.osm*. The output of this tool is *map-sanitized.net.xml* containing information about the road network, such as lanes and their connectivity, as well as commands for driving vehicles (the latter is not considered by this guide).
	
	```
	netconvert --osm-files map-sanitized.osm \ 
	-o map-sanitized.net.xml --output.street-names true \
	--output.original-names true
	```
	
4. Open *CityEngine* and create a new project together with an empty scene. Copy the *map-sanitized.osm* and  *map-sanitized.net.xml* in the **data** folder.

5. Drag-and-drop *map-sanitized.osm* in the empty scene. In the opened pop-up window select **only** the following options and click *Finish*:
	* **Select/deselect all** - all objects from the input are imported.
	* **Map OSM tags** - include the osm ID which is used to correlate between SUMO and CityEngine data in the export process.
	* **Run Graph Cleanup Tool after Import** - this is the only setting which does not alter important characteristics of the network elements such as osm ID and their position. If any nodes or segments are deleted in the CityEngine's import process or after that by the user, this will introduce inconsistencies with the map data imported in SUMO. If for some reason you want to change something in the map you have to either change the *map-sanitized.osm* or check the export output for warnings and decide how to solve them.
	* **Create Street/Intersection Shapes from Graph**

6. In the generated city model select the appropriate rules for every object in the scene and generate the textures using the *Generate* button.

7. To export the city model in Unity3D compatible format, firstly, select all shapes and go to *File > Export Model* and choose the *FBX* option. Use the default location (*models* folder) for all export files. Select **Center** button and note the **x** and **z** offset values, set **y** to 0. The exported files should be *<name>.fbx* and textures.

8. To export the semantical description of the road network use the *mmkexporter.py* script (*cityengine-mmk/scripts*). In lines 340 and 341 specify the path to *map-sanitized.osm* and *map-sanitized.net.xml* (relative to CityEngine project's folder) and in lines 345 and 346 define the **x** and **z** offset which you noted from the *FBX* export in the previous step. **Important:** The script will try to determine automatically the offset between SUMO and CityEngine data but if this does not succeed a warning message will be displayed in the console and the user has to manually enter *sumoox* and *sumooz* values in lines 351 and 352 and pass them to the *Exporter* object. Start the script either by selecting *Python > Run* or *F9*. The generated file can be found in *cityengine-mmk/export* and it is called by default *MMK_GraphExport.json*.

9. Import files in Unity3D by following the steps in this order:
	* Create a folder named *Assets/Models/\<name of scene\>*.
	* Create another folder named *Assets/Models/\<name of scene\>/Textures* and copy all pictures from the models folder in CityEngine to this folder.
	* Copy *<name>.fbx* file to *Assets/Models/\<name of scene\>* (the materials folder will be copied automatically).

10. Drag and drop the model to the Unity3D scene and add a *BoxCollider* to the ground of the scene. Next, change the scaling of the street model to (100, 100, 100). Attach to the model the *Network.cs* script and *CarRoadDescriptor.cs* script to **MMKCar**. In *Network.cs* specify the path to *MMK_GraphExport.json* and in *CarRoadDescriptor.cs* enter the name of the city model.
