﻿using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;
using System.IO;

public class NetworkDescription : MonoBehaviour
{
		enum NetworkComponentType { Edge, Node };

		string m_Path = "C:\\Users\\Zhechev\\Documents\\IDP\\MMK\\cityengine-mmk\\export\\MMK_GraphExport.json";
		Dictionary<string , GameObject> networkItems = new Dictionary<string , GameObject> ();

		List<Vector3> xs = new List<Vector3> ();
		List<Vector3> ys = new List<Vector3> ();

		void Start ()
		{
				string jsonExport;
				using (StreamReader r = new StreamReader (m_Path)) {
						jsonExport = r.ReadToEnd ();
				}

				var json = JSON.Parse (jsonExport);
				buildNetwork (json);
		}

		public GameObject GetNetworkItem (string id)
		{
				GameObject item;
				return networkItems.TryGetValue (id, out item) ? item : null;
		}

		private void buildNetwork (JSONNode root)
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

				// Debug Lanes
				if (type == NetworkComponentType.Edge) {
						NetworkEdge edge = (NetworkEdge)item;
						DebugDrawLanes (edge.forwardLanes);
						DebugDrawLanes (edge.backwardLanes);
				} else {
						DebugDrawLanes (((NetworkNode)item).lanes);
				}

				return roadElement;
		}

		private void DebugDrawLanes (List<NetworkLane> lanes)
		{
				if (lanes == null) {
						return;
				}

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
