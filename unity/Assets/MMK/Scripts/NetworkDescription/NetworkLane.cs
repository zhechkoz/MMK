using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkLane
{
		public string id;
		private int index;
		private double length;
		public List<Vector3> vertices = new List<Vector3> ();

		public NetworkLane (string id, int index, double length)
		{
				this.id = id;
				this.index = index;
				this.length = length;
		}

		public double GetLength ()
		{
				return length;
		}

		public int GetIndex ()
		{
				return index;
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
