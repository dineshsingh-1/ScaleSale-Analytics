# ScaleSale Web Application
# Upload your sales data and get instant insights!
# Author: Dinesh Singh Rajpurohit

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
import io

# ============================================
# PAGE CONFIGURATION
# ============================================
st.set_page_config(
    page_title="ScaleSale Analytics",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================
# CUSTOM CSS - FIXED VERSION
# ============================================
st.markdown("""
    <style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;600;700&display=swap');
    
    .stApp {
        font-family: 'Inter', sans-serif;
    }
    
    h1, h2, h3 {
        font-family: 'Inter', sans-serif;
        color: #1e3a8a;
    }
    
    .main > div {
        padding-top: 2rem;
    }
    
    .welcome-card {
        background: white;
        padding: 30px;
        border-radius: 12px;
        box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        text-align: center;
        height: 100%;
    }
    
    .welcome-card h2 {
        font-size: 48px;
        margin-bottom: 10px;
    }
    
    .welcome-card h3 {
        color: #1e3a8a;
        margin-bottom: 10px;
    }
    
    .blue-card {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
    }
    
    .green-card {
        background: linear-gradient(135deg, #dcfce7 0%, #bbf7d0 100%);
    }
    
    .yellow-card {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    }
    
    .feature-item {
        padding: 10px 0;
        font-size: 16px;
    }
    
    div[data-testid="stMetricValue"] {
        font-size: 28px;
        font-weight: 700;
    }
    </style>
""", unsafe_allow_html=True)

# ============================================
# HELPER FUNCTIONS
# ============================================
def analyze_sales_data(df):
    """Analyze uploaded sales data and return insights"""
    
    insights = {}
    
    # Basic metrics
    insights['total_revenue'] = df['SALES'].sum() if 'SALES' in df.columns else 0
    insights['total_orders'] = df['ORDERNUMBER'].nunique() if 'ORDERNUMBER' in df.columns else len(df)
    insights['total_customers'] = df['CUSTOMERNAME'].nunique() if 'CUSTOMERNAME' in df.columns else 0
    insights['avg_order_value'] = df.groupby('ORDERNUMBER')['SALES'].sum().mean() if 'ORDERNUMBER' in df.columns and 'SALES' in df.columns else 0
    
    # Product analysis
    if 'PRODUCTLINE' in df.columns and 'SALES' in df.columns:
        insights['top_product'] = df.groupby('PRODUCTLINE')['SALES'].sum().idxmax()
        insights['top_product_revenue'] = df.groupby('PRODUCTLINE')['SALES'].sum().max()
        insights['product_revenue'] = df.groupby('PRODUCTLINE')['SALES'].sum().sort_values(ascending=False)
    
    # Geographic analysis
    if 'COUNTRY' in df.columns and 'SALES' in df.columns:
        insights['top_country'] = df.groupby('COUNTRY')['SALES'].sum().idxmax()
        insights['top_country_revenue'] = df.groupby('COUNTRY')['SALES'].sum().max()
        insights['country_revenue'] = df.groupby('COUNTRY')['SALES'].sum().sort_values(ascending=False).head(10)
    
    # Time analysis
    if 'ORDERDATE' in df.columns:
        df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'], errors='coerce')
        df['YEAR_MONTH'] = df['ORDERDATE'].dt.to_period('M')
        insights['monthly_revenue'] = df.groupby('YEAR_MONTH')['SALES'].sum() if 'SALES' in df.columns else None
    
    # Customer segmentation
    if 'CUSTOMERNAME' in df.columns and 'SALES' in df.columns:
        customer_stats = df.groupby('CUSTOMERNAME')['SALES'].sum()
        
        def categorize_customer(revenue):
            if revenue > 100000:
                return 'VIP'
            elif revenue > 50000:
                return 'High Value'
            elif revenue > 20000:
                return 'Medium Value'
            else:
                return 'Low Value'
        
        insights['customer_segments'] = customer_stats.apply(categorize_customer).value_counts()
    
    # Deal size analysis
    if 'DEALSIZE' in df.columns and 'SALES' in df.columns:
        insights['dealsize_revenue'] = df.groupby('DEALSIZE')['SALES'].sum()
    
    return insights

def create_revenue_trend_chart(df):
    """Create revenue trend line chart"""
    if 'ORDERDATE' not in df.columns or 'SALES' not in df.columns:
        return None
    
    df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'], errors='coerce')
    monthly = df.groupby(df['ORDERDATE'].dt.to_period('M'))['SALES'].sum()
    monthly.index = monthly.index.to_timestamp()
    
    fig = go.Figure()
    fig.add_trace(go.Scatter(
        x=monthly.index,
        y=monthly.values,
        mode='lines+markers',
        name='Revenue',
        line=dict(color='#3b82f6', width=3),
        fill='tozeroy',
        fillcolor='rgba(59, 130, 246, 0.1)',
        marker=dict(size=8)
    ))
    
    fig.update_layout(
        title="Revenue Trend Over Time",
        xaxis_title="Month",
        yaxis_title="Revenue ($)",
        height=400,
        template='plotly_white',
        hovermode='x unified'
    )
    
    return fig

def create_product_chart(product_revenue):
    """Create product revenue bar chart"""
    fig = go.Figure()
    
    colors = ['#1e40af', '#3b82f6', '#60a5fa', '#93c5fd', '#bfdbfe', '#dbeafe', '#eff6ff']
    
    fig.add_trace(go.Bar(
        y=product_revenue.index,
        x=product_revenue.values,
        orientation='h',
        marker=dict(color=colors[:len(product_revenue)]),
        text=[f'${v:,.0f}' for v in product_revenue.values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Revenue by Product Line",
        xaxis_title="Revenue ($)",
        yaxis_title="Product Line",
        height=400,
        template='plotly_white'
    )
    
    return fig

def create_country_chart(country_revenue):
    """Create country revenue bar chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        y=country_revenue.index,
        x=country_revenue.values,
        orientation='h',
        marker=dict(
            color=country_revenue.values,
            colorscale='Oranges',
            showscale=False
        ),
        text=[f'${v:,.0f}' for v in country_revenue.values],
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Top 10 Countries by Revenue",
        xaxis_title="Revenue ($)",
        yaxis_title="Country",
        height=400,
        template='plotly_white'
    )
    
    return fig

def create_customer_segment_chart(segments):
    """Create customer segmentation chart"""
    fig = go.Figure()
    
    colors = {'VIP': '#ec4899', 'High Value': '#8b5cf6', 'Medium Value': '#f59e0b', 'Low Value': '#06b6d4'}
    segment_colors = [colors.get(seg, '#6b7280') for seg in segments.index]
    
    fig.add_trace(go.Bar(
        x=segments.index,
        y=segments.values,
        marker=dict(color=segment_colors),
        text=segments.values,
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Customer Segmentation",
        xaxis_title="Segment",
        yaxis_title="Number of Customers",
        height=400,
        template='plotly_white'
    )
    
    return fig

def create_dealsize_chart(dealsize_revenue):
    """Create deal size pie chart"""
    fig = go.Figure()
    
    fig.add_trace(go.Pie(
        labels=dealsize_revenue.index,
        values=dealsize_revenue.values,
        hole=0.4,
        marker=dict(colors=['#ef4444', '#8b5cf6', '#10b981']),
        textinfo='label+percent',
        textposition='outside'
    ))
    
    fig.update_layout(
        title="Revenue Distribution by Deal Size",
        height=400,
        template='plotly_white'
    )
    
    return fig

# ============================================
# MAIN APP
# ============================================

# Header
st.markdown("""
    <div style='text-align: center; padding: 30px; background: linear-gradient(135deg, #1e3a8a 0%, #3b82f6 100%); color: white; border-radius: 15px; margin-bottom: 30px;'>
        <h1 style='color: white; margin: 0; font-size: 42px;'>📊 ScaleSale Analytics Platform</h1>
        <p style='font-size: 18px; margin: 15px 0 0 0; opacity: 0.95;'>Upload your sales data and get instant business insights</p>
    </div>
""", unsafe_allow_html=True)

# Sidebar
with st.sidebar:
    st.markdown("### 📁 Upload Your Data")
    st.markdown("---")
    
    uploaded_file = st.file_uploader(
        "Choose a file",
        type=['csv', 'xlsx', 'xls'],
        help="Upload your sales data in CSV or Excel format"
    )
    
    st.markdown("---")
    st.markdown("### 📋 Required Columns")
    st.markdown("""
    Your file should contain:
    - **ORDERNUMBER** (Order ID)
    - **SALES** (Revenue amount)
    - **CUSTOMERNAME** (Customer name)
    - **ORDERDATE** (Date)
    - **PRODUCTLINE** (Product category)
    - **COUNTRY** (Location)
    
    *Optional: DEALSIZE, QUANTITYORDERED*
    """)
    
    st.markdown("---")
    st.markdown("### 👨‍💻 Built By")
    st.markdown("**Dinesh Singh Rajpurohit**")
    st.markdown("Data Analyst | JECRC University")
    st.markdown("[LinkedIn](https://www.linkedin.com/in/dinesh-singh-rajpurohit-9863ab290) | [GitHub](https://github.com/dineshsingh-1)")

# Main content
if uploaded_file is None:
    # Welcome screen
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown("""
            <div class='welcome-card blue-card'>
                <h2>📤</h2>
                <h3>Upload Data</h3>
                <p style='color: #1e40af;'>Drag and drop your CSV or Excel file to get started</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
            <div class='welcome-card green-card'>
                <h2>🔍</h2>
                <h3>Analyze</h3>
                <p style='color: #166534;'>Automatic data cleaning and comprehensive analysis</p>
            </div>
        """, unsafe_allow_html=True)
    
    with col3:
        st.markdown("""
            <div class='welcome-card yellow-card'>
                <h2>📊</h2>
                <h3>Get Insights</h3>
                <p style='color: #92400e;'>Interactive dashboard and downloadable reports</p>
            </div>
        """, unsafe_allow_html=True)
    
    st.markdown("<br>", unsafe_allow_html=True)
    
    # Features section
    st.markdown("---")
    st.markdown("## ✨ Platform Features")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.markdown("""
        <div class='feature-item'>📈 Revenue trend analysis</div>
        <div class='feature-item'>🏆 Top products & markets identification</div>
        <div class='feature-item'>👥 Customer segmentation (VIP, High, Medium, Low)</div>
        <div class='feature-item'>📅 Seasonal pattern detection</div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown("""
        <div class='feature-item'>💰 Deal size breakdown analysis</div>
        <div class='feature-item'>🌍 Geographic insights across markets</div>
        <div class='feature-item'>📊 Interactive, exportable charts</div>
        <div class='feature-item'>📥 Download cleaned data & reports</div>
        """, unsafe_allow_html=True)
    
    st.markdown("---")
    st.info("👆 Upload a file using the sidebar to begin your analysis!")

else:
    # File uploaded - process it
    try:
        # Read file - IMPROVED DATA HANDLING
        with st.spinner('Loading your data...'):
            if uploaded_file.name.endswith('.csv'):
                # Try different encodings for CSV files
                try:
                    df = pd.read_csv(uploaded_file, encoding='utf-8')
                except UnicodeDecodeError:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding='latin-1')
            else:
                df = pd.read_excel(uploaded_file)
        
        st.success(f"✅ File uploaded successfully! Found {len(df):,} rows and {len(df.columns)} columns.")
        
        # Show data preview
        with st.expander("👀 View Data Preview (First 10 rows)"):
            st.dataframe(df.head(10), use_container_width=True)
        
        # Data cleaning - IMPROVED VERSION
        with st.spinner("🧹 Cleaning and analyzing data..."):
            # Count missing values
            missing_count = df.isnull().sum().sum()
            if missing_count > 0:
                st.info(f"ℹ️ Found {missing_count:,} missing values. Cleaning data...")
            
            # Handle string columns properly - convert to string only if needed
            string_columns = ['ORDERNUMBER', 'CUSTOMERNAME', 'PRODUCTLINE', 'COUNTRY']
            for col in string_columns:
                if col in df.columns:
                    # Fill NaN first, then convert to string
                    df[col] = df[col].fillna('Unknown').astype(str).str.strip()
            
            # Handle numeric columns
            numeric_columns = ['SALES', 'QUANTITYORDERED']
            for col in numeric_columns:
                if col in df.columns:
                    # Convert to numeric, coercing errors to NaN, then fill with 0
                    df[col] = pd.to_numeric(df[col], errors='coerce').fillna(0)
            
            # Handle DEALSIZE if it exists
            if 'DEALSIZE' in df.columns:
                df['DEALSIZE'] = df['DEALSIZE'].fillna('Unknown').astype(str)
            
            # Handle ORDERDATE
            if 'ORDERDATE' in df.columns:
                df['ORDERDATE'] = pd.to_datetime(df['ORDERDATE'], errors='coerce')
                # Drop rows where ORDERDATE couldn't be parsed
                date_nulls = df['ORDERDATE'].isnull().sum()
                if date_nulls > 0:
                    st.warning(f"⚠️ Removed {date_nulls} rows with invalid dates")
                    df = df[df['ORDERDATE'].notna()]
            
            # Analyze data
            insights = analyze_sales_data(df)
        
        st.markdown("---")
        
        # KPI Cards
        st.markdown("## 📊 Key Performance Indicators")
        
        col1, col2, col3, col4 = st.columns(4)
        
        with col1:
            st.metric(
                label="💰 Total Revenue",
                value=f"${insights['total_revenue']:,.0f}"
            )
        
        with col2:
            st.metric(
                label="📦 Total Orders",
                value=f"{insights['total_orders']:,}"
            )
        
        with col3:
            st.metric(
                label="👥 Total Customers",
                value=f"{insights['total_customers']:,}"
            )
        
        with col4:
            st.metric(
                label="💵 Avg Order Value",
                value=f"${insights['avg_order_value']:,.0f}"
            )
        
        st.markdown("---")
        
        # Key Insights Panel
        st.markdown("## 💡 Key Business Insights")
        
        insight_col1, insight_col2 = st.columns(2)
        
        with insight_col1:
            if 'top_product' in insights:
                st.info(f"🏆 **Top Product:** {insights['top_product']} generates ${insights['top_product_revenue']:,.0f}")
        
        with insight_col2:
            if 'top_country' in insights:
                st.info(f"🌍 **Best Market:** {insights['top_country']} contributes ${insights['top_country_revenue']:,.0f}")
        
        st.markdown("---")
        
        # Charts
        st.markdown("## 📈 Visual Analytics")
        
        # Revenue Trend (full width)
        trend_chart = create_revenue_trend_chart(df)
        if trend_chart:
            st.plotly_chart(trend_chart, use_container_width=True)
        
        # Two column layout for charts
        chart_col1, chart_col2 = st.columns(2)
        
        with chart_col1:
            if 'product_revenue' in insights:
                product_chart = create_product_chart(insights['product_revenue'])
                st.plotly_chart(product_chart, use_container_width=True)
            
            if 'customer_segments' in insights:
                segment_chart = create_customer_segment_chart(insights['customer_segments'])
                st.plotly_chart(segment_chart, use_container_width=True)
        
        with chart_col2:
            if 'country_revenue' in insights:
                country_chart = create_country_chart(insights['country_revenue'])
                st.plotly_chart(country_chart, use_container_width=True)
            
            if 'dealsize_revenue' in insights:
                dealsize_chart = create_dealsize_chart(insights['dealsize_revenue'])
                st.plotly_chart(dealsize_chart, use_container_width=True)
        
        st.markdown("---")
        
        # Download section
        st.markdown("## 📥 Export Your Analysis")
        
        download_col1, download_col2 = st.columns(2)
        
        with download_col1:
            # Download cleaned data
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📄 Download Cleaned Data (CSV)",
                data=csv,
                file_name=f"scalesale_cleaned_{datetime.now().strftime('%Y%m%d')}.csv",
                mime="text/csv",
                use_container_width=True
            )
        
        with download_col2:
            # Download insights report
            report = f"""SCALESALE ANALYTICS REPORT
Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}
File: {uploaded_file.name}

{'='*60}
KEY METRICS
{'='*60}
Total Revenue: ${insights['total_revenue']:,.2f}
Total Orders: {insights['total_orders']:,}
Total Customers: {insights['total_customers']:,}
Average Order Value: ${insights['avg_order_value']:,.2f}

{'='*60}
TOP PERFORMERS
{'='*60}
Top Product: {insights.get('top_product', 'N/A')} (${insights.get('top_product_revenue', 0):,.2f})
Top Country: {insights.get('top_country', 'N/A')} (${insights.get('top_country_revenue', 0):,.2f})

{'='*60}
STRATEGIC RECOMMENDATIONS
{'='*60}
1. Focus marketing and inventory on top-performing products
2. Implement VIP customer retention program
3. Analyze seasonal trends for better planning
4. Consider expansion in underperforming markets
5. Review pricing strategy for different deal sizes

{'='*60}
Generated by ScaleSale Analytics Platform
Built by Dinesh Singh Rajpurohit
JECRC University | Data Analyst
{'='*60}
            """
            
            st.download_button(
                label="📊 Download Analysis Report (TXT)",
                data=report,
                file_name=f"scalesale_report_{datetime.now().strftime('%Y%m%d')}.txt",
                mime="text/plain",
                use_container_width=True
            )
    
    except Exception as e:
        st.error(f"❌ Error processing file: {str(e)}")
        st.info("💡 Please ensure your file contains the required columns: ORDERNUMBER, SALES, CUSTOMERNAME, ORDERDATE, PRODUCTLINE, COUNTRY")
        
        with st.expander("🔍 See detailed error"):
            st.code(str(e))

# Footer
st.markdown("---")
st.markdown("""
    <div style='text-align: center; color: #64748b; padding: 20px;'>
        <p style='margin: 5px 0;'><strong>ScaleSale Analytics Platform</strong></p>
        <p style='margin: 5px 0;'>Built with Python, Streamlit & Plotly</p>
        <p style='margin: 5px 0;'>© 2026 Dinesh Singh Rajpurohit | Data-Driven Business Intelligence</p>
    </div>
""", unsafe_allow_html=True)
