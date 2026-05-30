if st.button("✅ Submit"):
        if not existing_week_data.empty:
            duplicate_submission_dialog()
            st.stop()
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            others = st.session_state.cached_df[st.session_state.cached_df["Branch"] != st.session_state.selected_branch].copy()
            
            # Prepare new data
            new_data = edited_df.copy()
            new_data["Branch"] = st.session_state.selected_branch
            
            # Combine
            final = pd.concat([others, new_data], ignore_index=True)
            
            # --- FIX STARTS HERE ---
            # Create the mapping for days
            rename_map = {day: day_labels[day] for day in DAYS}
            # Ensure "Over-Time" is kept (rename it only if it exists, otherwise leave as is)
            if "Over-Time" not in rename_map:
                rename_map["Over-Time"] = "Over-Time"
            
            final = final.rename(columns=rename_map)
            # --- FIX ENDS HERE ---
            
            # Ensure 'Over-Time' column exists in final even if empty
            if "Over-Time" not in final.columns:
                final["Over-Time"] = "0 hrs"

            # Update Sheet
            ws.update([final.columns.tolist()] + final.fillna("").values.tolist())
            
            st.session_state.cached_df = final
            st.session_state.shift_buffer = {}
            st.session_state.deleted_staff = set()
            success_dialog()
        except Exception as e:
            st.error(f"❌ Submission Failed: {e}")if st.button("✅ Submit"):
        if not existing_week_data.empty:
            duplicate_submission_dialog()
            st.stop()
        try:
            ws = master_sheet.worksheet("StaffSchedule")
            others = st.session_state.cached_df[st.session_state.cached_df["Branch"] != st.session_state.selected_branch].copy()
            
            # Prepare new data
            new_data = edited_df.copy()
            new_data["Branch"] = st.session_state.selected_branch
            
            # Combine
            final = pd.concat([others, new_data], ignore_index=True)
            
            # --- FIX STARTS HERE ---
            # Create the mapping for days
            rename_map = {day: day_labels[day] for day in DAYS}
            # Ensure "Over-Time" is kept (rename it only if it exists, otherwise leave as is)
            if "Over-Time" not in rename_map:
                rename_map["Over-Time"] = "Over-Time"
            
            final = final.rename(columns=rename_map)
            # --- FIX ENDS HERE ---
            
            # Ensure 'Over-Time' column exists in final even if empty
            if "Over-Time" not in final.columns:
                final["Over-Time"] = "0 hrs"

            # Update Sheet
            ws.update([final.columns.tolist()] + final.fillna("").values.tolist())
            
            st.session_state.cached_df = final
            st.session_state.shift_buffer = {}
            st.session_state.deleted_staff = set()
            success_dialog()
        except Exception as e:
            st.error(f"❌ Submission Failed: {e}")
