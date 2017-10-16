using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkNode : NetworkItem
{
		public List<string> neighbourSegments;
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

		override public void DeserializeFromJSON (JSONNode nodeJSON)
		{
				this.id = nodeJSON ["id"];
				this.osmID = nodeJSON ["osm"].AsInt;
				this.hierarchy = nodeJSON ["hierarchy"];

				JSONArray jsonLanes = nodeJSON ["lanes"].AsArray;
				JSONArray jsonShapes = nodeJSON ["shapes"].AsArray;
				JSONArray jsonVertices = nodeJSON ["vertices"].AsArray;

				foreach (JSONNode jsonVertex in jsonVertices) {
						float x = jsonVertex ["x"].AsFloat;
						float y = jsonVertex ["y"].AsFloat;
						float z = jsonVertex ["z"].AsFloat;
						this.vertices.Add (new Vector3 (x, y, z));
				}

				if (jsonShapes != null) {
						foreach (JSONNode shapeJSON in jsonShapes.Children) {
								NetworkShape shape = NetworkShape.DeserializeFromJSON (shapeJSON); 
								this.shapes.Add (shape);
						}
				}
						
				if (jsonLanes != null) {
						foreach (JSONNode laneJSON in jsonLanes.Children) {
								NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
								this.lanes.Add (lane);
						}
				}
		}
}
