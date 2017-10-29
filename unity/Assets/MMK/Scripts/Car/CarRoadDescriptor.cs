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

				void Start ()
				{
						description = GameObject.Find ("tum_0").GetComponent<Network> ();
				}

				void Update ()
				{
						NetworkLane currentLane = null;
						NetworkItem currentItem = null;
						CurrentRoadInformation (out currentLane, out currentItem);
						Debug.Log (currentLane == null ? "No Lane" : currentLane.id);

						if (beenThere) {
								CalculateRouteTo (new Vector3 (30, 1, 30));
								beenThere = false;
						}
				}

				public List<Vector3> CalculateRouteTo (Vector3 destination)
				{
						NetworkLane currentLane;
						NetworkItem item;
						CurrentRoadInformation (out currentLane, out item);

						var destinationNetworItems = new List<NetworkItem> ();
						foreach (var collider in Physics.OverlapBox (destination, Vector3.one)) {
								item = collider.gameObject.GetComponent<NetworkItem> ();
								if (item != null) {
										destinationNetworItems.Add (item);
								}
						}

						NetworkLane destinationLane;
						RoadInformation (destination, destinationNetworItems, out destinationLane, out item);
						if (destinationLane == null) {
								Debug.Log ("Destination not on road!");
								return null;
						}

						List<NetworkLane> routeLanes = description.CalculateRoute (currentLane.id, destinationLane.id);
						if (routeLanes == null) {
								Debug.Log ("No route to destination!");
								return null;
						}

						List<Vector3> routePoints = ExtractRoutePoints (routeLanes, transform.position, destination);

						// Debug route
						xs.AddRange (routePoints);

						return routePoints;
				}

				private List<Vector3> ExtractRoutePoints (List<NetworkLane> routeLanes, Vector3 start, Vector3 end)
				{
						var result = new List<Vector3> ();
						var currentPosition = MMKExtensions.ToVector2 (start);
						var destinationPosition = MMKExtensions.ToVector2 (end);

						for (int i = 0; i < routeLanes.Count; i++) {
								var vertices = new List<Vector3>(routeLanes [i].vertices);
								if (i == 0) {
										int j = 0;
										for (; j < vertices.Count - 1; j++) {
												var laneA = MMKExtensions.ToVector2 (vertices [j]);
												var laneB = MMKExtensions.ToVector2 (vertices [j + 1]);
												if (Vector2.Dot (laneB - laneA, currentPosition - laneA) < 0) {
														break;
												}
										}
										vertices.RemoveRange (0, j);
								} 

								if (i == routeLanes.Count - 1) {
										int j = 0;
										for (; j < vertices.Count - 1; j++) {
												var laneA = MMKExtensions.ToVector2 (vertices [j]);
												var laneB = MMKExtensions.ToVector2 (vertices [j + 1]);
												if (Vector2.Dot (laneB - laneA, destinationPosition - laneA) < 0) {
														break;
												}
										}
										vertices.RemoveRange (j, vertices.Count - j);
								}
								result.AddRange (vertices); 
						}

						return result;
				}

				public void RoadInformation (Vector3 position, ICollection<NetworkItem> possibleItems, 
				                            out NetworkLane networkLane, out NetworkItem networkItem)
				{
						var currentPosition = MMKExtensions.ToVector2 (position);
						float minimalDistance = float.MaxValue;
						networkItem = null;
						networkLane = null;

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

				public void CurrentRoadInformation (out NetworkLane networkLane, out NetworkItem networkItem)
				{
						var currentItems = currentRoads.Values;
						RoadInformation (transform.position, currentItems, out networkLane, out networkItem);
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
						Color red = Color.red;
						Gizmos.color = red;
						for (int i = 0; i < xs.Count; i++) {
								Gizmos.DrawSphere (xs [i], 1.5f);	
						}
				}
		}
}
