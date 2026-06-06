# ── RESUME FIX: paste this entire cell into Colab and run ─────────────
# Fixes the num_workers crash and resumes from best checkpoint

# Reload best checkpoint
model.load_state_dict(torch.load('htc_outputs/best_model.pt'))

# Recreate loaders with num_workers=0 (fixes Colab multiprocessing crash)
tr_loader = DataLoader(tr_ds, batch_size=BATCH, sampler=sampler,
                       num_workers=0, pin_memory=False, drop_last=True)
te_loader = DataLoader(te_ds, batch_size=BATCH * 2, shuffle=False,
                       num_workers=0, pin_memory=False)

# Reset optimizer + scheduler for remaining 3 epochs
REMAINING = 3
optimizer = AdamW(model.parameters(), lr=1e-5, weight_decay=0.01)
n_steps = (len(tr_loader) // GRAD_ACCUM) * REMAINING
scheduler = get_cosine_schedule_with_warmup(optimizer,
    num_warmup_steps=int(n_steps * 0.05), num_training_steps=n_steps)
scaler = torch.cuda.amp.GradScaler()

best_f1 = 0.4449

for epoch in range(REMAINING):
    model.train()
    total_loss = 0
    optimizer.zero_grad()
    t0 = time.time()

    for step, (ids, mask, s_lbl, g_lbl, c_lbl) in enumerate(tqdm(tr_loader, desc=f'epoch {epoch+3}/{5}')):
        ids, mask = ids.to(device), mask.to(device)
        s_lbl, g_lbl, c_lbl = s_lbl.to(device), g_lbl.to(device), c_lbl.to(device)

        with torch.cuda.amp.autocast():
            s_logits, g_logits, c_logits, _ = model(ids, mask)
            loss = (W_SECTOR * loss_sector(s_logits, s_lbl) +
                    W_GROUP  * loss_group(g_logits, g_lbl) +
                    W_CODE   * loss_code(c_logits, c_lbl))
            loss = loss / GRAD_ACCUM

        scaler.scale(loss).backward()
        total_loss += loss.item() * GRAD_ACCUM

        if (step + 1) % GRAD_ACCUM == 0:
            scaler.unscale_(optimizer)
            torch.nn.utils.clip_grad_norm_(model.parameters(), 1.0)
            scaler.step(optimizer)
            scaler.update()
            optimizer.zero_grad()
            scheduler.step()

    avg_loss = total_loss / len(tr_loader)
    elapsed = time.time() - t0

    model.eval()
    all_preds, all_true, all_s_pred, all_s_true = [], [], [], []
    with torch.no_grad():
        for ids, mask, s_lbl, g_lbl, c_lbl in tqdm(te_loader, desc='eval'):
            ids, mask = ids.to(device), mask.to(device)
            with torch.cuda.amp.autocast():
                s_logits, g_logits, c_logits, _ = model(ids, mask)
            all_preds.extend(c_logits.argmax(dim=-1).cpu().tolist())
            all_true.extend(c_lbl.tolist())
            all_s_pred.extend(s_logits.argmax(dim=-1).cpu().tolist())
            all_s_true.extend(s_lbl.tolist())

    pred_codes = le_code.inverse_transform(all_preds)
    true_codes = le_code.inverse_transform(all_true)
    macro_f1 = f1_score(true_codes, pred_codes, average='macro', zero_division=0)
    acc = accuracy_score(true_codes, pred_codes)
    s_acc = accuracy_score(all_s_true, all_s_pred)

    print(f'\nepoch {epoch+3}: loss={avg_loss:.4f}  time={elapsed:.0f}s')
    print(f'  Sector accuracy : {s_acc*100:.2f}%')
    print(f'  Code Macro F1   : {macro_f1*100:.2f}%')
    print(f'  Code Accuracy   : {acc*100:.2f}%')

    if macro_f1 > best_f1:
        best_f1 = macro_f1
        torch.save(model.state_dict(), 'htc_outputs/best_model.pt')
        print(f'  ★ New best! Saved.')

print(f'\n{"="*60}')
print(f'BEST MACRO F1: {best_f1*100:.2f}%')
print(f'{"="*60}')
