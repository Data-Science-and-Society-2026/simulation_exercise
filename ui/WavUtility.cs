using System;
using System.IO;
using UnityEngine;

public static class WavUtility
{
    public static void Save(string filePath, AudioClip clip)
    {
        byte[] wavData = ConvertAudioClipToWav(clip);
        File.WriteAllBytes(filePath, wavData);
    }

    private static byte[] ConvertAudioClipToWav(AudioClip clip)
    {
        using (MemoryStream stream = new MemoryStream())
        {
            int sampleCount = clip.samples * clip.channels;
            int sampleRate = clip.frequency;
            int channels = clip.channels;

            using (BinaryWriter writer = new BinaryWriter(stream))
            {
                writer.Write(new char[4] { 'R', 'I', 'F', 'F' });
                writer.Write(36 + sampleCount * 2);
                writer.Write(new char[4] { 'W', 'A', 'V', 'E' });
                writer.Write(new char[4] { 'f', 'm', 't', ' ' });
                writer.Write(16);
                writer.Write((ushort)1);
                writer.Write((ushort)channels);
                writer.Write(sampleRate);
                writer.Write(sampleRate * channels * 2);
                writer.Write((ushort)(channels * 2));
                writer.Write((ushort)16);
                writer.Write(new char[4] { 'd', 'a', 't', 'a' });
                writer.Write(sampleCount * 2);

                float[] samples = new float[sampleCount];
                clip.GetData(samples, 0);

                foreach (float sample in samples)
                {
                    short sampleInt = (short)(sample * 32767);
                    writer.Write(sampleInt);
                }
            }

            return stream.ToArray();
        }
    }
}
