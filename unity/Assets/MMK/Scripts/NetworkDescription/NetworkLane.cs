using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkLane
{
		public string id { get; protected set; }
		public int index { get; protected set; }
		public double length { get; protected set; }
		public List<Vector3> vertices { get; protected set; }

		public NetworkLane (string id, int index, double length)
		{
				this.id = id;
				this.index = index;
				this.length = length;
				vertices = new List<Vector3> ();
		}

		public static NetworkLane DeserializeFromJSON (JSONNode laneJSON)
		{
				string id = laneJSON ["id"];
				int index = laneJSON ["lane"];
				double length = laneJSON ["length"];
				NetworkLane lane = new NetworkLane (id, index, length);

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
