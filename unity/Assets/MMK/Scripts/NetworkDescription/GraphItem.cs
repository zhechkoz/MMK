using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class GraphItem {
		private NetworkLane lane;
		private List<string> adjacentLanes;
		private Dictionary<string, List<NetworkLane>> via;

		public GraphItem(NetworkLane lane)
		{
				this.lane = lane;
				this.adjacentLanes = new List<string>();
				this.via = new Dictionary<string, List<NetworkLane>> ();
		}

		public double GetWeight() 
		{
				return lane.GetLength();
		}

		public string GetID() 
		{
				return lane.id;
		}

		public List<string> GetAdjacentLanes() 
		{
				return adjacentLanes;
		}

		public List<Vector3> GetPathToLane(string id) 
		{
				var path = new List<Vector3> ();
				path.AddRange (lane.vertices);

				List<NetworkLane> viaLanes;
				if (via.TryGetValue (id, out viaLanes)) {
						foreach (NetworkLane viaLane in viaLanes) {
								path.AddRange (viaLane.vertices);
						}
				}

				return path;
		}

		public void AppendLane(string id, List<NetworkLane> viaLanes) 
		{
				adjacentLanes.Add (id);
				if (viaLanes.Count > 0) {
						via.Add (id, viaLanes);
				}
		}

		public override string ToString() 
		{
				string output = lane.id + ": ";
				foreach (string laneID in adjacentLanes) {
						output += laneID + ", ";
				}

				return output;
		}
}
