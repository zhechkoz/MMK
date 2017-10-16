using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public abstract class NetworkItem : MonoBehaviour
{
		public string id;
		public int osmID;
		public string hierarchy;
		public List<Vector3> vertices = new List<Vector3> ();
		public List<NetworkShape> shapes = new List<NetworkShape> ();

		public abstract NetworkLane GetLaneByID (string id);

		public abstract void DeserializeFromJSON (JSONNode nodeJSON);

		public List<Vector3> GetBoxColliderSizeAndCenter ()
		{
				foreach (NetworkShape shape in shapes) {
						// Only the first shape represents roads
						if (shape.id.EndsWith (":0")) {
								return shape.CalculateExtendedAABB ();
						}
				}
				return null;
		}
}
