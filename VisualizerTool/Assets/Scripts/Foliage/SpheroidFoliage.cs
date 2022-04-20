using System.Collections;
using System.Collections.Generic;
using UnityEngine;
using Sirenix.OdinInspector;

// Super ellipse equation:
// https://www.desmos.com/calculator/byif8mjgy3

public class SpheroidFoliage : FoliageBase
{
    [Range(0, 64)] public int sampleRate = 6;
    [Range(0.1f, 10f)] public float upperCurv = 0.5f;
    [Range(0.1f, 10f)] public float lowerCurv = 0.5f;
    // [Range(0.1f, 10f)] public float curvature = 0.5f;


    public float SampleSuperEllipse(float value01)
    {
        float x = Mathf.Clamp01(value01);
        bool invert = (x <= 0.5f);
        float curvature = (invert) ? lowerCurv : upperCurv;
        x = Mathf.Abs((x - 0.5f) * 2.0f);

        float y = Mathf.Pow((1f - Mathf.Pow(x , curvature)), 1f / curvature);
        if (invert) y = -y;
        return y;
    }

    public override Vector3[] GenerateProfile()
    {
        Vector3[] profile = new Vector3[2 + sampleRate];
        profile[0] = new Vector3(0f, offset);

        for (int i = 1; i < profile.Length - 1; i++)
        {
            profile[i] = new Vector3(
                radius * Mathf.Abs(SampleSuperEllipse((i - 1) / (float)(sampleRate - 1))),
                height * ((i - 1) / (float)(sampleRate - 1)) + offset);
        }
        profile[profile.Length - 1] = new Vector3(0f, offset + height);

        return profile;
    }
}