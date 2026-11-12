// Exporta del juego original lo que necesita mk_sprites.py: tabla de sprites, fuente pequeña y paginas de textura.
using System;
using System.IO;
using System.Text;
using System.Collections.Generic;
using UndertaleModLib.Util;
string W = Environment.GetEnvironmentVariable("TB_WORK");
Directory.CreateDirectory(W + "/spr"); Directory.CreateDirectory(W + "/fg"); Directory.CreateDirectory(W + "/pages");
var tw = new TextureWorker();
// 1) sprites de los menus de controles y pausa
var sb = new StringBuilder();
var names = new HashSet<string>();
foreach (var o in Data.GameObjects) {
  if (o.Name.Content.StartsWith("obj_control") || o.Name.Content.StartsWith("obj_controls")) {
    sb.AppendLine("OBJ " + o.Name.Content + " -> " + o.Sprite?.Name?.Content);
    if (o.Sprite != null) names.Add(o.Sprite.Name.Content);
  }
}
foreach (var n in new[]{"spr_pause_menu_frame","spr_pause_menu_map_locked","spr_pause_menu_colorswap","spr_file_select_menu_new"}) names.Add(n);
foreach (var n in names) {
  var s = Data.Sprites.ByName(n); if (s == null) { sb.AppendLine("MISSING " + n); continue; }
  sb.AppendLine("SPR " + n + " " + s.Width + "x" + s.Height + " frames " + s.Textures.Count + " origin " + s.OriginX + "," + s.OriginY);
  for (int i = 0; i < s.Textures.Count; i++) {
    var t = s.Textures[i].Texture;
    sb.AppendLine("  F" + i + " page " + Data.EmbeddedTextures.IndexOf(t.TexturePage) + " src " + t.SourceX + "," + t.SourceY + " " + t.SourceWidth + "x" + t.SourceHeight + " tgt " + t.TargetX + "," + t.TargetY + " " + t.TargetWidth + "x" + t.TargetHeight + " bb " + t.BoundingWidth + "x" + t.BoundingHeight);
  }
}
File.WriteAllText(W + "/spr/list.txt", sb.ToString());
// 2) fuente font_small
sb = new StringBuilder();
var f = Data.Fonts.ByName("font_small"); var ft = f.Texture;
sb.AppendLine("FONT font_small page " + Data.EmbeddedTextures.IndexOf(ft.TexturePage) + " tex " + ft.SourceX + "," + ft.SourceY + " " + ft.SourceWidth + "x" + ft.SourceHeight);
foreach (var g in f.Glyphs) sb.AppendLine("  G " + g.Character + " " + g.SourceX + "," + g.SourceY + " " + g.SourceWidth + "x" + g.SourceHeight + " shift " + g.Shift + " off " + g.Offset);
File.WriteAllText(W + "/fg/list.txt", sb.ToString());
tw.ExportAsPNG(ft, W + "/fg/font_small_tex.png");
// 3) paginas de textura
for (int n = 30; n <= 42; n++) {
  using (var fs = File.Create(W + "/pages/" + n + ".png")) { Data.EmbeddedTextures[n].TextureData.Image.SavePng(fs); }
}
