using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;
using System.IO;

public class NetworkDescription : MonoBehaviour
{

		string m_Path = "C:\\Users\\Zhechev\\Documents\\IDP\\MMK\\cityengine-mmk\\export\\MMK_GraphExport.json";
		Dictionary<string , NetworkItem> networkItems = new Dictionary<string , NetworkItem> ();

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

		public NetworkItem getNetworkItem (string id)
		{
				NetworkItem item;
				return networkItems.TryGetValue (id, out item) ? item : null;
		}

		private void buildNetwork (JSONNode root)
		{
				GameObject networkDescription = new GameObject ("RoadsDescription");
				foreach (JSONNode segmentJSON in root ["segments"].AsArray.Children) {
						NetworkEdge edge = NetworkEdge.DeserializeFromJSON (segmentJSON);
						createGameObject (edge, networkDescription);
						networkItems.Add (edge.id, edge);
						debugDrawLanes (edge.forwardLanes);
						debugDrawLanes (edge.backwardLanes);
				}

				foreach (JSONNode nodeJSON in root ["nodes"].AsArray.Children) {
						NetworkNode node = NetworkNode.DeserializeFromJSON (nodeJSON);
						createGameObject (node, networkDescription);
						networkItems.Add (node.id, node);
						debugDrawLanes (node.lanes);
				}
		}

		private void createGameObject (NetworkItem item, GameObject parent)
		{
				List<Vector3> centerSizeBoundingBox = item.GetBoxColliderSizeAndCenter ();

				if (centerSizeBoundingBox != null) {
						GameObject roadSegment = new GameObject (item.id);
						roadSegment.transform.parent = parent.transform;
						BoxCollider collider = roadSegment.AddComponent<BoxCollider> ();
						collider.isTrigger = true;
						collider.center = centerSizeBoundingBox [0];
						collider.size = centerSizeBoundingBox [1];	
				}
		}

		private void debugDrawLanes (List<NetworkLane> lanes)
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
