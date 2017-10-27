using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Priority_Queue;

namespace MMK.Car
{
		public class CarRoadDescriptor : MonoBehaviour
		{
				Dictionary<string, NetworkItem> currentRoads = new Dictionary<string,NetworkItem> ();
				bool beenThere = true;
				void Update ()
				{
						string id = "";
						NetworkItem networkItem = null;
						//CurrentRoadInformation (out id, out networkItem);
						//Debug.Log (id);
						if (beenThere) {
								getPath (":2285938307_0_0", "392103894#1_0");
								beenThere = false;
						}
				}

				public void CurrentRoadInformation (out string laneID, out NetworkItem networkItem)
				{
						Vector3 currentPosition = this.transform.position;
						float minimalDistance = float.MaxValue;

						laneID = null;
						networkItem = null;

						foreach (NetworkItem item in currentRoads.Values) {
								List<NetworkLane> lanes = new List<NetworkLane> ();
								lanes.AddRange (item.GetAllLanes ());

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

				public void getPath (string startID, string endID)
				{
						var tum = GameObject.Find ("tum_0").GetComponent<NetworkDescription> ().graph;
						var q = new SimplePriorityQueue<GraphItem> ();
						var distances = new Dictionary<string, double> ();
						var previous = new Dictionary<string, string> ();

						var start = tum [startID];
						q.Enqueue (start, 0);

						distances [startID] = 0;

						while (q.Count > 0) {
								var current = q.Dequeue ();
								if (current.GetID () == endID) {
										List<string> path = new List<string> ();

										string id = current.GetID ();
										while (previous.ContainsKey (id)) {
												path.Add (id);
												id = previous [id];
										}
										path.Add (startID);
										path.Reverse ();
										foreach (string p in path) {
												Debug.Log (p);
										}

										break;
								}

								//Debug.Log (current.GetID());

								foreach (string id in current.GetAdjacentLanes()) {
										double newDist = distances[current.GetID()] + current.GetWeight ();
										double oldDistance;

										if (!distances.TryGetValue(id, out oldDistance) || newDist < oldDistance) {
												previous [id] = current.GetID();
												//Debug.Log (oldDistance);
												if (oldDistance == 0) {
														q.Enqueue (tum [id], (float) newDist);
												} else {
														q.TryUpdatePriority (tum [id], (float) newDist);
												}
												distances [id] = newDist;
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
						GameObject networkElement = other.gameObject;
						string id = networkElement.name;
						NetworkItem item = networkElement.GetComponent<NetworkItem> ();
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
}
