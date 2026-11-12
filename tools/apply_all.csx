// Aplica todos los cambios al game.droid: texturas, glifos, sprites en castellano y codigo.
using System;
using System.IO;
using System.Linq;
using System.Collections.Generic;
using UndertaleModLib.Util;
using UndertaleModLib.Models;
using UndertaleModLib.Compiler;
string W = Environment.GetEnvironmentVariable("TB_WORK");
// 1) paginas de textura modificadas
foreach (var fpng in Directory.GetFiles(W + "/pages_out", "*.png")) {
  int n = int.Parse(Path.GetFileNameWithoutExtension(fpng));
  var img = GMImage.FromPng(File.ReadAllBytes(fpng));
  var ms = new MemoryStream();
  Data.EmbeddedTextures[n].TextureData.Image = img.ConvertToBz2Qoi(ms);
}
// 2) glifos nuevos (a e i o u n ! ?) en las fuentes
foreach (var line in File.ReadAllLines(W + "/fonts_add.txt")) {
  var p = line.Split('\t');
  var font = Data.Fonts.ByName(p[1]);
  if (p[0] == "range") { font.RangeEnd = uint.Parse(p[2]); continue; }
  var gl = new UndertaleFont.Glyph();
  gl.Character = ushort.Parse(p[2]);
  gl.SourceX = ushort.Parse(p[3]); gl.SourceY = ushort.Parse(p[4]);
  gl.SourceWidth = ushort.Parse(p[5]); gl.SourceHeight = ushort.Parse(p[6]);
  gl.Shift = short.Parse(p[7]); gl.Offset = short.Parse(p[8]);
  var all = font.Glyphs.ToList(); all.Add(gl);
  all = all.OrderBy(x => x.Character).ToList();
  font.Glyphs.Clear();
  foreach (var x in all) font.Glyphs.Add(x);
}
// 3) sprites en castellano (_es)
var byName = new Dictionary<string, SortedDictionary<int, int[]>>();
foreach (var line in File.ReadAllLines(W + "/meta.txt")) {
  var p = line.Split(' ');
  if (p.Length < 6) continue;
  if (!byName.ContainsKey(p[0])) byName[p[0]] = new SortedDictionary<int, int[]>();
  byName[p[0]][int.Parse(p[1])] = new[]{int.Parse(p[2]), int.Parse(p[3]), int.Parse(p[4]), int.Parse(p[5])};
}
var grp = Data.TextureGroupInfo.First(g => g.Name.Content == "Default");
foreach (var kv in byName) {
  var o = Data.Sprites.ByName(kv.Key);
  var n = new UndertaleSprite();
  n.Name = Data.Strings.MakeString(kv.Key + "_es");
  n.Width = o.Width; n.Height = o.Height;
  n.MarginLeft = o.MarginLeft; n.MarginRight = o.MarginRight; n.MarginTop = o.MarginTop; n.MarginBottom = o.MarginBottom;
  n.Transparent = o.Transparent; n.Smooth = o.Smooth; n.Preload = o.Preload;
  n.BBoxMode = o.BBoxMode; n.SepMasks = o.SepMasks;
  n.OriginX = o.OriginX; n.OriginY = o.OriginY;
  n.SVersion = o.SVersion; n.SSpriteType = o.SSpriteType;
  n.GMS2PlaybackSpeed = o.GMS2PlaybackSpeed; n.GMS2PlaybackSpeedType = o.GMS2PlaybackSpeedType;
  for (int i = 0; i < o.Textures.Count; i++) {
    var ot = o.Textures[i].Texture;
    var r = kv.Value[i];
    var t = new UndertaleTexturePageItem();
    t.SourceX = (ushort)r[0]; t.SourceY = (ushort)r[1]; t.SourceWidth = (ushort)r[2]; t.SourceHeight = (ushort)r[3];
    t.TargetX = ot.TargetX; t.TargetY = ot.TargetY; t.TargetWidth = ot.TargetWidth; t.TargetHeight = ot.TargetHeight;
    t.BoundingWidth = ot.BoundingWidth; t.BoundingHeight = ot.BoundingHeight;
    t.TexturePage = Data.EmbeddedTextures[33];
    Data.TexturePageItems.Add(t);
    n.Textures.Add(new UndertaleSprite.TextureEntry { Texture = t });
  }
  foreach (var m in o.CollisionMasks) n.CollisionMasks.Add(new UndertaleSprite.MaskEntry { Data = (byte[])m.Data.Clone() });
  Data.Sprites.Add(n);
  grp.Sprites.Add(new UndertaleResourceById<UndertaleSprite, UndertaleChunkSPRT> { Resource = n });
}
// 4) codigo
var g2 = new CodeImportGroup(Data);
foreach (var fgml in Directory.GetFiles(W + "/patched", "*.gml")) g2.QueueReplace(Path.GetFileNameWithoutExtension(fgml), File.ReadAllText(fgml));
g2.Import();
