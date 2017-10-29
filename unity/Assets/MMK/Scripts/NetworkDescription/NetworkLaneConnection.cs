using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class NetworkLaneConnection {
		public NetworkLane lane { get; private set; }
		public List<string> adjacentLanes { get; private set; }
		private Dictionary<string, List<NetworkLane>> via;

		public double weight { get { return lane.length;} }
		public string id {get { return lane.id; } }

		public NetworkLaneConnection(NetworkLane lane)
		{
				this.lane = lane;
				this.adjacentLanes = new List<string>();
				this.via = new Dictionary<string, List<NetworkLane>> ();
		}

		// TODO: Dijkstra will return only lanes; this calculation
		// will be done in car according to the returned lanes
		/*
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
		}*/

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
						output += laneID + " ";
				}

				return output;
		}
}
