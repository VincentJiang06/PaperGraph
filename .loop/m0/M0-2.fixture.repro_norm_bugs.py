# Two minimal, self-contained reproductions of defects in 01-CONTRACTS §1.2.2 as written.
import norm

print("### BUG 1: 中文專項規則是非對稱的 -- 中文文檔裡的純英文引語永遠無法命中")
snap = "本文提出的方法 optimal transport 在数据集上取得了最好效果。"
q = "optimal transport"
print("  snapshot      = %r" % snap)
print("  quote         = %r" % q)
print("  raw substring = %s" % (q in snap))
print("  as_written    : quote_key=%r" % norm.compare_key(q))
print("                  snap_key =%r" % norm.compare_key(snap))
print("                  pass=%s" % norm.quote_faithful(q, snap, False, norm.compare_key))
print("  fix_adjacent  : quote_key=%r" % norm.compare_key_v3(q))
print("                  snap_key =%r" % norm.compare_key_v3(snap))
print("                  pass=%s" % norm.quote_faithful(q, snap, False, norm.compare_key_v3))

print()
print("### BUG 2: 跨行連字符還原不保子串 -- 引語在還原窗口內被截斷即失配")
snap2 = "spanning English, Chinese, Spanish, French, German, Arabic, Rus-\nsian, Korean"
q2 = "German, Arabic, Rus-\n"
print("  snapshot      = %r" % snap2)
print("  quote         = %r" % q2)
print("  raw substring = %s" % (q2 in snap2))
print("  as_written    : quote_key=%r" % norm.compare_key(q2, True))
print("                  snap_key =%r" % norm.compare_key(snap2, True))
print("                  pass=%s" % norm.quote_faithful(q2, snap2, True, norm.compare_key))
print("  fix_adjacent  : pass=%s" % norm.quote_faithful(q2, snap2, True, norm.compare_key_v3))

print()
print("### 對照: 修正規則不會把拉丁詞邊界吃掉（不能讓 'the rapist' 命中 'therapist'）")
print("  as_written   'the rapist' in '...therapist...' (中文文檔) ->",
      norm.quote_faithful("the rapist", "他是 a therapist 。", False, norm.compare_key))
print("  fix_adjacent 'the rapist' in '...therapist...' (中文文檔) ->",
      norm.quote_faithful("the rapist", "他是 a therapist 。", False, norm.compare_key_v3))
