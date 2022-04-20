using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

[System.Serializable]
public class CurveFoliage : FoliageBase
{
    public AnimationCurve curve;
    [Range(0, 64)] public int sampleRate = 6;

    public override Vector3[] GenerateProfile()
    {
        Vector3[] profile = new Vector3[2 + sampleRate];
        profile[0] = new Vector3(0f, offset);

        for (int i = 1; i < profile.Length - 1; i++)
        {
            profile[i] = new Vector3(
                radius * Mathf.Abs(curve.Evaluate((i - 1) / (float)(sampleRate - 1))),
                height * ((i - 1) / (float)(sampleRate - 1)) + offset);
        }
        profile[profile.Length - 1] = new Vector3(0f, offset + height);

        return profile;
    }
}