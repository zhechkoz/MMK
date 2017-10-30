using System.Collections;
using System.Collections.Generic;
using UnityEngine;

using Network = MMK.NetworkDescription.Network;
using NetworkItem = MMK.NetworkDescription.NetworkItem;
using NetworkLane = MMK.NetworkDescription.NetworkLane;

namespace MMK.Car
{
		public class CarRoadDescriptor : MonoBehaviour
		{
				private Dictionary<string, NetworkItem> currentRoads = new Dictionary<string, NetworkItem> ();

				bool beenThere = true;
				Network description;
				List<Vector3> xs = new List<Vector3> ();
				Vector3 aim = new Vector3 (206, 1, 235);

				void Start ()
				{
						description = GameObject.Find ("tum_0").GetComponent<Network> ();
				}

				void Update ()
				{
						NetworkLane currentLane = null;
						NetworkItem currentItem = null;
						CurrentRoadPosition (out currentLane, out currentItem);
						Debug.Log (currentLane == null ? "No Lane" : currentLane.id);

						if (beenThere) {
								CalculateRouteTo (aim);
								beenThere = false;
						}
				}

				public List<Vector3> CalculateRouteTo (Vector3 destination)
				{
						NetworkLane currentLane;
						NetworkItem item;
						CurrentRoadPosition (out currentLane, out item);

						// Calculate the nearest lane to the destination by checking
						// whether it intersects any BoxColliders which belong to a NetworkItems.
						var destinationNetworItems = new List<NetworkItem> ();
						foreach (var collider in Physics.OverlapBox (destination, Vector3.one)) {
								item = collider.gameObject.GetComponent<NetworkItem> ();
								if (item != null) {
										destinationNetworItems.Add (item);
								}
						}

						NetworkLane destinationLane;
						RoadPosition (destination, destinationNetworItems, out destinationLane, out item);
						if (destinationLane == null) {
								Debug.Log ("Destination not on road!");
								return null;
						}

						// Calculate route lanes by using the CalculateRoute method in Network.
						List<NetworkLane> routeLanes = description.CalculateRoute (currentLane.id, destinationLane.id);
						if (routeLanes == null) {
								Debug.Log ("No route to destination!");
								return null;
						}

						// Finally calculate the drivable points from the correct lanes
						List<Vector3> routePoints = ExtractRoutePoints (routeLanes, transform.position, destination);

						// Debug route
						xs.AddRange (routePoints);

						return routePoints;
				}

				private List<Vector3> ExtractRoutePoints (List<NetworkLane> routeLanes, Vector3 start, Vector3 end)
				{
						var result = new List<Vector3> ();
						var startPosition = MMKExtensions.ToVector2 (start);
						var endPosition = MMKExtensions.ToVector2 (end);

						// Traverse all lanes and add their vertices to result;
						// Start and End lane are processed in the following different way:
						// We remove all vertices behind the start position and after the
						// end position.
						for (int i = 0; i < routeLanes.Count; i++) {
								var vertices = routeLanes [i].vertices;

								// Check if we handle the first or last lane 
								if (i == 0 || i == routeLanes.Count - 1) {
										// If so, make a copy of the lane's vertices
										vertices = new List<Vector3> (routeLanes [i].vertices);
										int j;
										if (i == 0) {
												for (j = 0; j < vertices.Count - 1; j++) {
														var laneA = MMKExtensions.ToVector2 (vertices [j]);
														var laneB = MMKExtensions.ToVector2 (vertices [j + 1]);
														if (Vector2.Dot (laneB - laneA, startPosition - laneA) < 0) {
																break; // Start already is after/at laneA-laneB line 
														}
												}
												vertices.RemoveRange (0, j); // Remove all vertices which are behind the start
										} 

										if (i == routeLanes.Count - 1) {
												for (j = 0; j < vertices.Count - 1; j++) {
														var laneA = MMKExtensions.ToVector2 (vertices [j]);
														var laneB = MMKExtensions.ToVector2 (vertices [j + 1]);
														if (Vector2.Dot (laneB - laneA, endPosition - laneA) < 0) {
																break; // End is already behind/at laneA-laneB line
														}
												}
												vertices.RemoveRange (j, vertices.Count - j); // Remove all vertices which are after the end
										}
								}
								result.AddRange (vertices); 
						}

						return result;
				}

				public void RoadPosition (Vector3 position, ICollection<NetworkItem> possibleItems, 
				                          out NetworkLane networkLane, out NetworkItem networkItem)
				{
						var currentPosition = MMKExtensions.ToVector2 (position);
						float minimalDistance = float.MaxValue;
						networkItem = null;
						networkLane = null;

						// Traverse all lanes and find the nearest
						foreach (NetworkItem item in possibleItems) {
								foreach (NetworkLane lane in item.GetAllLanes ()) {
										List<Vector3> vertices = lane.vertices;
										for (int i = 0; i < vertices.Count - 1; i++) {
												var laneA = MMKExtensions.ToVector2 (vertices [i]);
												var laneB = MMKExtensions.ToVector2 (vertices [i + 1]);
												float currentDistance = Mathf.Abs (MMKExtensions.DistanceLineToPoint (laneA, laneB, currentPosition, true));
												if (currentDistance < minimalDistance) {
														minimalDistance = currentDistance;
														networkLane = lane;
														networkItem = item;
												}
										}
								}
						}
				}

				public void CurrentRoadPosition (out NetworkLane networkLane, out NetworkItem networkItem)
				{
						var currentItems = currentRoads.Values;
						RoadPosition (transform.position, currentItems, out networkLane, out networkItem);
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

				void OnDrawGizmos ()
				{
						Gizmos.color = Color.red;
						for (int i = 0; i < xs.Count; i++) {
								Gizmos.DrawSphere (xs [i], 1.5f);	
						}
								
						Gizmos.color = Color.blue;
						Gizmos.DrawSphere (aim, 1.5f);
				}
		}
}
