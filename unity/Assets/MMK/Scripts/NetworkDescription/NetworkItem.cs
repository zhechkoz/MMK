using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using SimpleJSON;

public class NetworkItem : MonoBehaviour {
		public string id;
		public int osmID;
		protected string hierarchy;
		public List<Vector3> vertices = new List<Vector3> ();
		public List<NetworkShape> shapes = new List<NetworkShape> ();

		public List<Vector3> getBoxColliderSizeAndCenter() {
				foreach(NetworkShape shape in shapes) {
						if (shape.id.EndsWith (":0")) {
								return shape.calculateAABB ();
						}
				}
				return null;
		}
}
