#!/bin/bash

# SAS Hash Object 論文批量下載腳本
# 直接下載所有 11 篇論文到本地資料夾

mkdir -p downloaded_papers

echo "🚀 開始下載 11 篇論文..."
echo ""

# 第一批：核心論文
echo "📚 第一批：核心論文 (4 篇)"
echo "================================"

echo "1️⃣  下載 The SAS Hash Object in Action..."
curl -L "https://www.academia.edu/download/48795576/HOW009.Dorfman.pdf" -o "downloaded_papers/01_SAS_Hash_Object_in_Action.pdf" 2>/dev/null

echo "2️⃣  下載 Data Aggregation Using the SAS Hash Object..."
curl -L "https://pages.mini.pw.edu.pl/~jablonskib/SASpublic/WUSS2024_125/(Dorfman%20and%20Henderson%202015)%20Paul%20M.%20Dorfman,%20Don%20Henderson,%20Data%20Aggregation%20Using%20the%20SAS%20Hash%20Object.pdf" -o "downloaded_papers/02_Data_Aggregation_Hash_Object.pdf" 2>/dev/null

echo "3️⃣  下載 Beyond Table Lookup: The Versatile SAS Hash Object..."
curl -L "https://www.beoptimized.be/pdf/Paper_821-2017.pdf" -o "downloaded_papers/03_Beyond_Table_Lookup.pdf" 2>/dev/null

echo "4️⃣  下載 Hash Crash and Beyond..."
curl -L "https://www.academia.edu/download/48795585/037-2008.pdf" -o "downloaded_papers/04_Hash_Crash_Beyond.pdf" 2>/dev/null

echo ""
echo "📈 第二批：進階論文 (4 篇)"
echo "================================"

echo "5️⃣  下載 Data Step Hash Objects as Programming Tools..."
curl -L "https://www.academia.edu/download/48874866/236-30.pdf" -o "downloaded_papers/05_Hash_Objects_Programming_Tools.pdf" 2>/dev/null

echo "6️⃣  下載 User-Defined Multithreading with the SAS DS2 Procedure..."
curl -L "https://proceedings.wuss.org/2019/161_Final_Paper_PDF.pdf" -o "downloaded_papers/06_DS2_Multithreading.pdf" 2>/dev/null

echo "7️⃣  下載 Using PROC FCMP to the Fullest..."
curl -L "https://proceedings.wuss.org/2019/73_Final_Paper_PDF.pdf" -o "downloaded_papers/07_PROC_FCMP_Fullest.pdf" 2>/dev/null

echo "8️⃣  下載 Five Reasons To Swipe Right on PROC FCMP..."
curl -L "https://sesug.org/proceedings/sesug_2024_SAAG/PresentationSummaries/Papers/141_Final_PDF.pdf" -o "downloaded_papers/08_FCMP_Five_Reasons.pdf" 2>/dev/null

echo ""
echo "📚 第三批：補充論文 (3 篇)"
echo "================================"

echo "9️⃣  下載 User-Written DATA Step Functions..."
curl -L "https://pages.mini.pw.edu.pl/~jablonskib/SASpublic/WUSS2024_125/(Secosky%202007)%20Jason%20Secosky,%20User-Written%20DATA%20Step%20Functions.pdf" -o "downloaded_papers/09_User_Written_Functions.pdf" 2>/dev/null

echo "🔟 下載 Top Ten SAS Performance Tuning Techniques..."
curl -L "https://www.lexjansen.com/wuss/2016/38_Final_Paper_PDF.pdf" -o "downloaded_papers/10_Performance_Tuning.pdf" 2>/dev/null

echo "1️⃣1️⃣ 下載 The SQL Optimizer Project..."
curl -L "https://www.beoptimized.be/pdf/SUGI30_101.pdf" -o "downloaded_papers/11_SQL_Optimizer_Project.pdf" 2>/dev/null

echo ""
echo "✅ 完成！所有論文已下載到 downloaded_papers/ 資料夾"
echo ""
echo "📋 下載結果："
ls -lh downloaded_papers/
echo ""
echo "💡 下一步：把這些 PDF 上傳到你的 Google Drive 資料夾"
echo "   https://drive.google.com/drive/folders/1Xd5UZk0rEJ0hhqmGzt88DP7hNWbz3Fuf"
