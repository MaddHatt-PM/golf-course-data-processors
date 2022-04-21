using System.IO;
using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

#if UNITY_EDITOR
using UnityEditor;
#endif

public class PerlinCSVGenerator : MonoBehaviour
{
    public TextAsset target;
    public TextAsset targetInfo;

    

    public float width = 10f;
    public float length = 15f;
    public Vector2 offset;
    public float sampleDistance = 1f;

    public bool autorefresh = false;

    void OnValidate()
    {
        if (autorefresh) Generate();
    }

    [Button("Generate")]
    public void Generate()
    {
        string targetContents = "[X]-Latitude,[Y]-Longitude,[Z]-Elevation\n";
        Vector3 pos = Vector3.zero;
        // float seed = Random.Range(0f, 999f);
        int xIter = 0, yIter = 0;

        for (float x = 0f; x < width; x += width / sampleDistance)
        {
            xIter++;
            yIter = 0;
            for (float y = 0f; y < length; y += length / sampleDistance)
            {
                pos.x = x;
                pos.y = y;
                pos.z = Mathf.PerlinNoise((pos.x + offset.x), (pos.y + offset.y));

                targetContents += string.Format("{0},{1},{2}\n", pos.x, pos.y, pos.z);
                yIter++;
            }
        }

        targetContents = targetContents.Remove(targetContents.Length - 1);

#if UNITY_EDITOR
        File.WriteAllText(AssetDatabase.GetAssetPath(target), targetContents);
        EditorUtility.SetDirty(target);
#endif

        string infoContents = "X-SampleCount, Y-SampleCount\n";
        infoContents += string.Format("{0},{1}", xIter, yIter);

#if UNITY_EDITOR
        File.WriteAllText(AssetDatabase.GetAssetPath(targetInfo), infoContents);
        EditorUtility.SetDirty(targetInfo);

        AssetDatabase.Refresh();
#endif
    }
}