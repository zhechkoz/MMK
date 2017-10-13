using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkNode : NetworkItem {
		List<string> neighbourSegments;
		public List<NetworkLane> lanes;

		public static NetworkNode deserializeFromJSON(JSONNode nodeJSON)
		{
				NetworkNode node = new NetworkNode ();
				node.id = nodeJSON ["ID"];
				node.osmID = nodeJSON ["osm"].AsInt;
				node.hierarchy = nodeJSON ["hierarchy"];

				JSONArray lanes = nodeJSON ["lanes"].AsArray;
				JSONArray shapes = nodeJSON ["shapes"].AsArray;
				JSONArray vertices = nodeJSON ["vertices"].AsArray;

				JSONArray jsonVertices = nodeJSON ["vertices"].AsArray;
				foreach (JSONNode jsonVertex in jsonVertices) {
						float x = jsonVertex ["x"].AsFloat;
						float y = jsonVertex ["y"].AsFloat;
						float z = jsonVertex ["z"].AsFloat;
						node.vertices.Add (new Vector3 (x, y, z));
				}

				if (shapes != null && shapes.Count > 0) {
						foreach (JSONNode shapeJSON in shapes.Children) {
								NetworkShape shape = NetworkShape.deserializeFromJSON (shapeJSON); 
								node.shapes.Add (shape);
						}
				}
						
				if (lanes != null && lanes.Count > 0) {
						node.lanes = new List<NetworkLane> ();
						foreach (JSONNode laneJSON in lanes.Children) {
								NetworkLane lane = NetworkLane.deserializeFromJSON (laneJSON);
								node.lanes.Add (lane);
						}
				}
				return node;
		}
}
