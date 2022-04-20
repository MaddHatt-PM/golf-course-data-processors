using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

[System.Serializable]
public abstract class FoliageBase
{
    public float radius;
    public float height;
    public float offset;
    [Range(3, 64)] public int revolutionCount = 8;

    public abstract Vector3[] GenerateProfile();
    public virtual bool IsInCollider(Vector3 point)
    {
        if (point.y >= offset && point.y <= offset + height)
        {
            // Convert point to polar in respect to foliage origin
            Vector3 polarPoint = MathUtilities.CartesianToPolar(point);

            Vector3[] profile = GenerateProfile();
            int rangeID;
            for (rangeID = 1; rangeID < profile.Length - 2; rangeID++)
                if (profile[rangeID].y <= point.y && point.y <= profile[rangeID + 1].y)
                    break;

            float sectionRadius = Mathf.Lerp(
                profile[rangeID].x,
                profile[rangeID + 1].x,
                (point.y - offset) / (profile[rangeID + 1].x - profile[rangeID].x)
            );

            if (polarPoint.x <= sectionRadius)
                return true;
        }

        return false;
    }

    public virtual Mesh GenerateMesh(Mesh mesh)
    {
        if (mesh == null) mesh = new Mesh();
        mesh.Clear();

        List<Vector3> verts = new List<Vector3>();
        List<int> tris = new List<int>();

        Vector3[] strip = GenerateProfile();
        int stripCt = strip.Length - 2; // disregard the start/end points
        for (int i = 1; i < strip.Length - 1; i++)
        {
            strip[i] = MathUtilities.CartesianToPolar(strip[i]);
            if (i != 0 && i != strip.Length - 1)
                verts.Add(strip[i]);
        }

        // Add and connect non pole vertices
        for (int revID = 1; revID < revolutionCount; revID++)
        {
            // Add to vertices
            for (int pID = 1; pID < strip.Length - 1; pID++)
            {
                strip[pID].z = (Mathf.PI * 2f) / revolutionCount * revID;
                verts.Add(MathUtilities.PolarToCartesian(strip[pID]));
            }

            // Add triangles
            int initPoint = (revID - 1) * stripCt;
            for (int pID = 0; pID < Mathf.Max(stripCt - 1, 2); pID += 1)
            {
                tris.Add(pID + initPoint + 0); tris.Add(pID + initPoint + 1); tris.Add(pID + initPoint + stripCt);
                tris.Add(pID + initPoint + 1); tris.Add(pID + initPoint + 1 + stripCt); tris.Add(pID + initPoint + stripCt);
            }
        }

        // Connect the start and end loops
        int endStripOffset = verts.Count - stripCt;
        for (int i = 0; i < stripCt - 1; i++)
        {
            tris.Add(i + 1); tris.Add(i); tris.Add(i + endStripOffset);
            tris.Add(i + endStripOffset); tris.Add(i + 1 + endStripOffset); tris.Add(i + 1);
        }

        // Add bottom pole and tris
        verts.Add(strip[0]);
        int btmVertID = verts.Count - 1;
        for (int i = 0; i < revolutionCount - 1; i++)
        {
            tris.Add(btmVertID);
            tris.Add((i * stripCt));
            tris.Add((i * stripCt) + stripCt);
        }

        tris.Add(btmVertID);
        tris.Add((revolutionCount - 1) * stripCt);
        tris.Add(0);

        // // // Add top pole and tris
        verts.Add(strip[strip.Length - 1]);
        int topVertID = verts.Count - 1;
        int stripOffset = stripCt - 1;
        for (int i = 0; i < revolutionCount - 1; i++)
        {
            tris.Add((i * stripCt) + (stripCt - 1) + stripCt);
            tris.Add((i * stripCt) + (stripCt - 1));
            tris.Add(topVertID);
        }

        tris.Add((stripCt - 1));
        tris.Add(topVertID);
        tris.Add(verts.Count - 3);

        // Finalize mesh
        mesh.vertices = verts.ToArray();
        mesh.triangles = tris.ToArray();
        mesh.RecalculateNormals();

        return mesh;
    }
}
