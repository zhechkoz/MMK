using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkEdge : NetworkItem {
		string start;
		string end;
		double length;
		double maxSpeed;
		bool oneway;
		string hierarchy;
		List<Vector3> vertices = new List<Vector3>();
		public List<NetworkLane> forwardLanes;
		public List<NetworkLane> backwardLanes;

		public List<Vector3> getBoxColliderSizeAndCenter() {
				foreach(NetworkShape shape in shapes) {
						if (shape.id.EndsWith (":0")) {
								return shape.calculateAABB ();
						}
				}
				return null;
		}

		public static NetworkEdge deserializeFromJSON(JSONNode segmentJSON)
		{
				NetworkEdge segment = new NetworkEdge ();
				segment.id = segmentJSON ["ID"];
				segment.osmID = segmentJSON ["osm"].AsInt;
				segment.start = segmentJSON ["start"];
				segment.end = segmentJSON ["end"];
				segment.length = segmentJSON ["length"].AsDouble;
				segment.maxSpeed = segmentJSON ["maxspeed"].AsDouble;
				segment.hierarchy = segmentJSON ["hierarchy"];
				segment.oneway = segmentJSON ["oneway"] != null && segmentJSON ["oneway"].AsBool;
						
				JSONArray forward = segmentJSON ["lanes"] ["forward"].AsArray;
				JSONArray backward = segmentJSON ["lanes"] ["backward"].AsArray;
				JSONArray shapes = segmentJSON ["shapes"].AsArray;

				JSONArray jsonVertices = segmentJSON ["vertices"].AsArray;
				foreach (JSONNode jsonVertex in jsonVertices) {
						float x = jsonVertex ["x"].AsFloat;
						float y = jsonVertex ["y"].AsFloat;
						float z = jsonVertex ["z"].AsFloat;
						segment.vertices.Add (new Vector3 (x, y, z));
				}

				if (shapes != null && shapes.Count > 0) {
						foreach (JSONNode shapeJSON in shapes.Children) {
								NetworkShape shape = NetworkShape.deserializeFromJSON (shapeJSON); 
								segment.shapes.Add (shape);
						}
				}

				if (forward != null && forward.Count > 0) {
						segment.forwardLanes = new List<NetworkLane> ();
						foreach (JSONNode laneJSON in forward.Children) {
								NetworkLane lane = NetworkLane.deserializeFromJSON (laneJSON);
								segment.forwardLanes.Add (lane);
						}
				}

				if (backward != null && backward.Count > 0) {
						segment.backwardLanes = new List<NetworkLane> ();
						foreach (JSONNode laneJSON in backward.Children) {
								NetworkLane lane = NetworkLane.deserializeFromJSON (laneJSON);
								segment.backwardLanes.Add (lane);
						}
				}
				return segment;
		}
	
}
