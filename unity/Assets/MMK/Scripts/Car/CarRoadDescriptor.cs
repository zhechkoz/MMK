using System.Collections;
using System.Collections.Generic;
using UnityEngine;

public class CarRoadDescriptor : MonoBehaviour
{
		[SerializeField] public GameObject network;
		Dictionary<string, NetworkItem> currentRoads = new Dictionary<string,NetworkItem> ();

		void Update ()
		{
				string id = "";
				NetworkItem networkItem = null;
				CurrentRoadInformation (out id, out networkItem);
				Debug.Log (id);
		}

		public void CurrentRoadInformation (out string laneID, out NetworkItem networkItem)
		{
				Dictionary<string, NetworkItem>.ValueCollection values = currentRoads.Values;
				Vector3 currentPosition = this.transform.position;
				float minimalDistance = float.MaxValue;

				laneID = null;
				networkItem = null;

				foreach (NetworkItem item in values) {
						List<NetworkLane> lanes = new List<NetworkLane> ();
						if (item is NetworkEdge) {
								NetworkEdge edge = (NetworkEdge)item;
								List<NetworkLane> lanesForward = ((NetworkEdge)item).forwardLanes;
								List<NetworkLane> lanesBackward = ((NetworkEdge)item).backwardLanes;
								lanes.AddRange (lanesForward);
								lanes.AddRange (lanesBackward);
						} else if (item is NetworkNode) {
								List<NetworkLane> nodeLanes = ((NetworkNode)item).lanes;
								lanes.AddRange (nodeLanes);
						}

						foreach (NetworkLane lane in lanes) {
								List<Vector3> vertices = lane.vertices;
								for (int i = 0; i < vertices.Count - 1; i++) {
										float currentDistance = DistanceLineToPoint (currentPosition, vertices [i], vertices [i + 1]);
										if (currentDistance < minimalDistance) {
												minimalDistance = currentDistance;
												laneID = lane.id;
												networkItem = item;
										}
								}
						}
				}
		}

		// Calculates distance from Point A to line BC
		private float DistanceLineToPoint (Vector3 pointA, Vector3 lineB, Vector3 lineC)
		{
				Vector3 d = (lineC - lineB) / Vector3.Distance (lineC, lineB);
				Vector3 v = pointA - lineB;
				float t = Vector3.Dot (v, d);
				Vector3 P = lineB + new Vector3 (t * d.x, t * d.y, t * d.z);
				return Vector3.Distance (P, pointA);
		}

		void OnTriggerEnter (Collider other)
		{
				string id = other.gameObject.name;
				NetworkItem item = network.GetComponent<NetworkDescription> ().getNetworkItem (id);
				if (item != null && !currentRoads.ContainsKey (id)) {
						currentRoads.Add (id, item);
				}
		}

		void OnTriggerExit (Collider other)
		{
				string id = other.gameObject.name;
				if (currentRoads.ContainsKey (id)) {
						currentRoads.Remove (id);
				}
		}
}
