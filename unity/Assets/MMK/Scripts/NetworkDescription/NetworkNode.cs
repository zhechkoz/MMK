using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkNode : NetworkItem
{
		List<string> neighbourSegments;
		public List<NetworkLane> lanes = new List<NetworkLane> ();

		override public NetworkLane GetLaneByID (string id)
		{
				foreach (NetworkLane lane in lanes) {
						if (lane.id == id) {
								return lane;
						}
				}

				return null;
		}

		public static NetworkNode DeserializeFromJSON (JSONNode nodeJSON)
		{
				NetworkNode node = new NetworkNode ();
				node.id = nodeJSON ["id"];
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
								NetworkShape shape = NetworkShape.DeserializeFromJSON (shapeJSON); 
								node.shapes.Add (shape);
						}
				}
						
				if (lanes != null && lanes.Count > 0) {
						foreach (JSONNode laneJSON in lanes.Children) {
								NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
								node.lanes.Add (lane);
						}
				}
				return node;
		}
}
