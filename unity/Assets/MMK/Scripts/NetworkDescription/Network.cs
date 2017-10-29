﻿using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;
using Priority_Queue;
using System.IO;

namespace MMK.NetworkDescription
{
		public class Network : MonoBehaviour
		{
				private enum NetworkComponentType { Edge, Node };

				string m_Path = "C:\\Users\\Zhechev\\Documents\\IDP\\MMK\\cityengine-mmk\\export\\MMK_GraphExport.json";
				private Dictionary<string , GameObject> networkItems = new Dictionary<string , GameObject> ();

				private Dictionary<string, NetworkLaneConnection> connectivityGraph = new Dictionary<string, NetworkLaneConnection> ();
				private Dictionary<string , NetworkLane> lanes = new Dictionary<string , NetworkLane> ();

				private List<Vector3> xs = new List<Vector3> ();
				private List<Vector3> ys = new List<Vector3> ();

				void Start ()
				{
						string jsonExport;
						using (StreamReader r = new StreamReader (m_Path)) {
								jsonExport = r.ReadToEnd ();
						}

						var json = JSON.Parse (jsonExport);
						BuildNetwork (json);
						BuildConnectivityGraph (json);
				}

				public NetworkItem GetNetworkItemByID (string id)
				{
						GameObject item;
						return networkItems.TryGetValue (id, out item) ? item.GetComponent<NetworkItem> () : null;
				}

				public NetworkLane GetLaneByID (string id)
				{
						NetworkLane lane;
						return lanes.TryGetValue (id, out lane) ? lane : null;
				}

				private void BuildNetwork (JSONNode root)
				{
						GameObject networkDescription = new GameObject ("RoadsDescription");

						foreach (JSONNode segmentJSON in root ["segments"].AsArray.Children) {
								GameObject roadSegment = 
										CreateGameObject (NetworkComponentType.Edge, segmentJSON, networkDescription);
								networkItems.Add (roadSegment.name, roadSegment);
						}

						foreach (JSONNode nodeJSON in root ["nodes"].AsArray.Children) {
								GameObject roadSegment = 
										CreateGameObject (NetworkComponentType.Node, nodeJSON, networkDescription);
								networkItems.Add (roadSegment.name, roadSegment);
						}
				}

				private void BuildConnectivityGraph (JSONNode root)
				{
						foreach (JSONNode connectionJSON in root["connections"].AsArray.Children) {
								string fromLaneID = connectionJSON ["fromLane"];
								string toLaneID = connectionJSON ["toLane"];

								List<NetworkLane> viaLanes = new List<NetworkLane> ();
								foreach (string laneID in connectionJSON ["via"].AsArray.Children) {
										NetworkLane viaLane = GetLaneByID (laneID);
										if (viaLane == null) {
												Debug.Log ("viaLane does not exist!");
												continue;
										}
										viaLanes.Add (viaLane);
								}

								NetworkLaneConnection connection;
								if (connectivityGraph.TryGetValue (fromLaneID, out connection)) {
										connection.AppendLane (toLaneID, viaLanes);
								} else {
										NetworkLane fromLane = GetLaneByID (fromLaneID);

										if (fromLane == null) {
												Debug.Log ("Lane " + fromLaneID + " does not exist!");
												continue;
										}

										connection = new NetworkLaneConnection (fromLane);
										connection.AppendLane (toLaneID, viaLanes);
										connectivityGraph.Add (fromLaneID, connection);
								}

								if (!connectivityGraph.ContainsKey (toLaneID)) {
										NetworkLane toLane = GetLaneByID (toLaneID);
										if (toLane == null) {
												Debug.Log ("Lane " + toLaneID + " does not exist!");
												continue;
										}
										connectivityGraph.Add (toLaneID, new NetworkLaneConnection (toLane));
								}
						}
				}

				private GameObject CreateGameObject (NetworkComponentType type, JSONNode jsonData, GameObject parent)
				{		
						GameObject roadElement = new GameObject ();
						NetworkItem item;
						if (type == NetworkComponentType.Edge) {
								item = roadElement.AddComponent<NetworkEdge> ();
						} else {
								item = roadElement.AddComponent<NetworkNode> ();
						}

						item.DeserializeFromJSON (jsonData);
						roadElement.name = item.id;
						roadElement.transform.parent = parent.transform;
						List<Vector3> centerSizeBoundingBox = item.GetBoxColliderSizeAndCenter ();

						if (centerSizeBoundingBox != null) {
								BoxCollider collider = roadElement.AddComponent<BoxCollider> ();
								collider.isTrigger = true;
								collider.center = centerSizeBoundingBox [0];
								collider.size = centerSizeBoundingBox [1];	
						}

						// Manage Lanes
						List<NetworkLane> itemLanes = item.GetAllLanes ();
						itemLanes.ForEach (lane => lanes [lane.id] = lane);

						DebugDrawLanes (itemLanes); // Draws lanes for debug

						return roadElement;
				}

				public List<NetworkLane> CalculateRoute (string startID, string endID)
				{
						var q = new SimplePriorityQueue<NetworkLaneConnection> ();
						var distances = new Dictionary<string, double> ();
						var previous = new Dictionary<string, NetworkLane> ();

						NetworkLaneConnection start;
						if (!connectivityGraph.TryGetValue (startID, out start)) {
								Debug.Log ("Start node was not found!");
								return null;
						}

						distances [startID] = 0;
						q.Enqueue (start, distances [startID]);

						while (q.Count > 0) {
								var current = q.Dequeue ();
								if (current.id == endID) {
										return BacktrackRoute (current.lane, previous);
								}

								foreach (string id in current.adjacentLanes) {
										double newDist = distances [current.id] + current.weight;

										if (!distances.ContainsKey (id) || newDist < distances [id]) {
												previous [id] = current.lane;
												if (!distances.ContainsKey (id)) {
														q.Enqueue (connectivityGraph [id], newDist);
												} else {
														q.TryUpdatePriority (connectivityGraph [id], newDist);
												}
												distances [id] = newDist;
										}
								}
						}

						return null;
				}

				private List<NetworkLane> BacktrackRoute (NetworkLane end, Dictionary<string, NetworkLane> previous)
				{
						var route = new List<NetworkLane> ();
						route.Add (end);

						string id = end.id;
						NetworkLane previousLane;

						while (previous.ContainsKey (id)) {
								previousLane = previous [id];
								route.Add (previousLane);
								id = previousLane.id;
						}

						route.Reverse ();

						return route;
				}

				private void DebugDrawLanes (ICollection<NetworkLane> lanes)
				{
						foreach (NetworkLane lane in lanes) {
								List<Vector3> vertices = lane.vertices;
								Vector3 prev = vertices [0];
								Vector3 next;

								for (int i = 1; i < vertices.Count; i++) {
										next = vertices [i];
										xs.Add (next);
										ys.Add (prev);
										prev = next;
								}
						}
				}

				void OnDrawGizmos ()
				{
						Color red = new Color (1f, 0f, 0f);
						Gizmos.color = red;
						for (int i = 0; i < xs.Count; i++) {
								Gizmos.DrawLine (xs [i], ys [i]);	
						}
				}
		}
}
				