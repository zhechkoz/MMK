using System.Collections;
using System.Collections.Generic;
using UnityEngine;

namespace MMK.NetworkDescription
{
		public class NetworkLaneConnection
		{
				public NetworkLane lane { get; private set; }
				public List<string> adjacentLanes { get; private set; }
				public Dictionary<string, List<NetworkLane>> via { get; private set; }
				public string id { get { return lane.id; } }

				public NetworkLaneConnection (NetworkLane lane)
				{
						this.lane = lane;
						this.adjacentLanes = new List<string> ();
						this.via = new Dictionary<string, List<NetworkLane>> ();
				}

				public double Weight(string toLane) 
				{
						double weight = lane.length;
						List<NetworkLane> viaLanes;
						// Lane's own length + possible via lanes to the adjacent lane
						if (via.TryGetValue (toLane, out viaLanes)) {
								viaLanes.ForEach (l => weight += l.length);
						}

						return weight;
				}

				public void AppendLane (string id, List<NetworkLane> viaLanes)
				{
						adjacentLanes.Add (id);
						if (viaLanes.Count > 0) {
								via.Add (id, viaLanes);
						}
				}

				public override string ToString ()
				{
						string output = lane.id + ": ";
						foreach (string laneID in adjacentLanes) {
								output += laneID + " ";
						}

						return output;
				}
		}
}
