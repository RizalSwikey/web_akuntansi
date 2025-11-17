
```
accounting_apps
├─ .python-version
├─ .vscode
│  └─ settings.json
├─ core
│  ├─ admin.py
│  ├─ apps.py
│  ├─ migrations
│  │  ├─ 0001_initial.py
│  │  ├─ 0002_revenueitem_description.py
│  │  ├─ 0003_remove_revenueitem_description_and_more.py
│  │  ├─ 0004_expenseitem_expense_category_and_more.py
│  │  ├─ 0005_financialreport_ptkp_status.py
│  │  ├─ 0006_hppmanufacturefinishedgoods_hppmanufacturelabor_and_more.py
│  │  ├─ 0007_hppmanufacturematerial_diskon_and_more.py
│  │  ├─ 0008_hppmanufacturematerial_nama_bahan_baku.py
│  │  ├─ 0009_hppmanufacturematerial_keterangan.py
│  │  ├─ 0010_hppmanufacturewip_harga_satuan_and_more.py
│  │  ├─ 0011_hppmanufacturelabor_harga_satuan_and_more.py
│  │  ├─ 0012_hppmanufactureoverhead_harga_satuan_and_more.py
│  │  ├─ 0013_hppmanufacturefinishedgoods_harga_satuan_and_more.py
│  │  ├─ 0014_hppmanufactureproduction.py
│  │  ├─ 0015_alter_hppmanufactureproduction_unique_together.py
│  │  ├─ 0016_expenseitem_product_expenseitem_scope.py
│  │  ├─ 0017_alter_hppmanufactureoverhead_report.py
│  │  ├─ 0018_remove_financialreport_omzet_and_more.py
│  │  └─ __init__.py
│  ├─ models.py
│  ├─ static
│  │  └─ core
│  │     ├─ img
│  │     │  ├─ Bottom.jpg
│  │     │  ├─ j.ico
│  │     │  ├─ jurnalkita.png
│  │     │  ├─ jurnalkita_word.png
│  │     │  ├─ left.jpg
│  │     │  ├─ logo_jurnalkita.jpg
│  │     │  └─ right.jpg
│  │     └─ js
│  │        ├─ beban_usaha.js
│  │        ├─ profile.js
│  │        └─ sidebar.js
│  ├─ templates
│  │  └─ core
│  │     ├─ pages
│  │     │  ├─ beban_usaha.html
│  │     │  ├─ beban_usaha_manufaktur.html
│  │     │  ├─ hpp.html
│  │     │  ├─ hpp_manufaktur.html
│  │     │  ├─ landing_page.html
│  │     │  ├─ laporan.html
│  │     │  ├─ laporan_manufaktur.html
│  │     │  ├─ login.html
│  │     │  ├─ pendapatan.html
│  │     │  ├─ profile.html
│  │     │  └─ report_list.html
│  │     ├─ partials
│  │     │  ├─ login_message.html
│  │     │  └─ sidebar.html
│  │     └─ pdf
│  │        ├─ laporan_manufaktur_pdf.html
│  │        └─ laporan_pdf.html
│  ├─ templatetags
│  │  ├─ core_tags.py
│  │  └─ __init__.py
│  ├─ tests
│  │  ├─ test_hpp_calculator.py
│  │  └─ __init__.py
│  ├─ urls.py
│  ├─ utils
│  │  ├─ excel_exporter.py
│  │  ├─ final_report.py
│  │  ├─ hpp_calculator.py
│  │  ├─ pdf_exporter.py
│  │  └─ __init__.py
│  ├─ views.py
│  └─ __init__.py
├─ docker-compose.yaml
├─ Dockerfile.django
├─ Dockerfile.tailwind
├─ Makefile
├─ manage.py
├─ Procfile.tailwind
├─ pyproject.toml
├─ README.md
├─ requirements.txt
├─ sites
│  ├─ asgi.py
│  ├─ settings.py
│  ├─ urls.py
│  ├─ wsgi.py
│  └─ __init__.py
├─ staticfiles
│  ├─ admin
│  │  ├─ css
│  │  │  ├─ autocomplete.css
│  │  │  ├─ base.css
│  │  │  ├─ changelists.css
...............
│  │           └─ xregexp.min.js
│  ├─ core
│  │  ├─ img
│  │  │  ├─ Bottom.jpg
│  │  │  ├─ j.ico
│  │  │  ├─ jurnalkita.png
│  │  │  ├─ jurnalkita_word.png
│  │  │  ├─ left.jpg
│  │  │  ├─ logo_jurnalkita.jpg
│  │  │  └─ right.jpg
│  │  └─ js
│  │     ├─ beban_usaha.js
│  │     ├─ hpp.js
│  │     ├─ pendapatan.js
│  │     ├─ profile.js
│  │     └─ sidebar.js
│  ├─ css
│  └─ django-browser-reload
│     ├─ reload-listener.js
│     └─ reload-worker.js
├─ theme
│  ├─ apps.py
│  ├─ static
│  │  └─ css
│  ├─ static_src
│  │  ├─ package-lock.json
│  │  ├─ package.json
│  │  ├─ postcss.config.js
│  │  └─ src
│  │     └─ styles.css
│  ├─ templates
│  │  └─ base.html
│  └─ __init__.py
└─ uv.lock

```