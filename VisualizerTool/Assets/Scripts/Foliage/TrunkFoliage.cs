using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

[System.Serializable]
public class TrunkFoliage : FoliageBase
{
    [Range(0f, 1f)] public float lowerTaper = 0f;
    [Range(0f, 1f)] public float upperTaper = 0f;

    // Might good to cache this later on
    public override Vector3[] GenerateProfile()
    {
        Vector3[] profile = new Vector3[]
        {
            new Vector3(0f, offset),
            new Vector3(radius * (1f - lowerTaper), offset),
            new Vector3(radius * (1f - upperTaper), offset + height),
            new Vector3(0f, offset + height)
        };

        return profile;
    }
}