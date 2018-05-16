using System.Collections;
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

				public TextAsset jsonData;
				private Dictionary<string , GameObject> networkItems = new Dictionary<string , GameObject> ();

				private Dictionary<string, NetworkLaneConnection> connectivityGraph = new Dictionary<string, NetworkLaneConnection> ();
				private Dictionary<string , NetworkLane> lanes = new Dictionary<string , NetworkLane> ();
				private float xOffset, yOffset;

				void Start ()
				{
						var json = JSON.Parse (jsonData.ToString());
						BuildNetwork (json);
						BuildConnectivityGraph (json);
						GetOffsets(json);
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
						foreach (JSONNode laneJSON in root ["lanes"].AsArray.Children) {
								NetworkLane lane = NetworkLane.DeserializeFromJSON (laneJSON);
								lanes [lane.id] = lane;
						}

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

				private void GetOffsets(JSONNode root)
				{
					xOffset = root["offsets"]["sumo"]["x"].AsFloat;
					yOffset = root["offsets"]["sumo"]["z"].AsFloat;
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

						item.DeserializeFromJSON (jsonData, lanes);
						roadElement.name = item.id;
						roadElement.transform.parent = parent.transform;
						List<Vector3> centerSizeBoundingBox = item.GetBoxColliderSizeAndCenter ();

						if (centerSizeBoundingBox != null) {
								BoxCollider collider = roadElement.AddComponent<BoxCollider> ();
								collider.isTrigger = true;
								collider.center = centerSizeBoundingBox [0];
								collider.size = centerSizeBoundingBox [1];	
						}

						return roadElement;
				}

				public List<NetworkLane> CalculateRoute (string startID, string endID)
				{
						var q = new SimplePriorityQueue<NetworkLaneConnection> ();
						var distances = new Dictionary<string, double> ();
						var previous = new Dictionary<string, NetworkLaneConnection> ();

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
										return BacktrackRoute (current, previous);
								}

								foreach (string id in current.adjacentLanes) {
										double newDist = distances [current.id] + current.Weight(id);

										if (!distances.ContainsKey (id) || newDist < distances [id]) {
												previous [id] = current;
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

				private List<NetworkLane> BacktrackRoute (NetworkLaneConnection end, Dictionary<string, NetworkLaneConnection> previous)
				{
						var route = new List<NetworkLane> ();
						route.Add (end.lane);

						string id = end.id;
						NetworkLaneConnection previousLane;

						while (previous.ContainsKey (id)) {
								previousLane = previous [id];
								List<NetworkLane> viaLanes;
								if (previousLane.via.TryGetValue(id, out viaLanes)) {
										viaLanes.Reverse ();
										foreach (NetworkLane viaLane in viaLanes) {
												route.Add (viaLane);
										}
								}

								route.Add (previousLane.lane);
								id = previousLane.id;
						}

						route.Reverse ();

						return route;
				}

				public Vector3 ConvertSumoCoordinatesToUnity(float sumoPositionX, float sumoPositionY, float gameObjectHeight)
				{
					float x = -sumoPositionX + xOffset;
					float y = gameObjectHeight / 2;
					float z = -sumoPositionY + yOffset;

					return new Vector3(x, y, z);
				}

				public float ConvertSumoAngleToUnity(float angle)
				{
					return (angle + 180.0f);
				}
		}
}
				