using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkLane : MonoBehaviour {
		public string id;
		int index;
		double length;
		public List<Vector3> vertices = new List<Vector3> ();

		public static NetworkLane deserializeFromJSON(JSONNode laneJSON)
		{
				NetworkLane lane = new NetworkLane ();
				lane.id = laneJSON["ID"];
				lane.index = laneJSON["lane"];
				lane.length = laneJSON["length"];
				JSONArray jsonVertices = laneJSON ["vertices"].AsArray;
				foreach (JSONNode jsonVertex in jsonVertices) {
						float x = jsonVertex ["x"].AsFloat;
						float y = jsonVertex ["y"].AsFloat;
						float z = jsonVertex ["z"].AsFloat;
						lane.vertices.Add (new Vector3 (x, y, z));
				}
				return lane;
		}
}
