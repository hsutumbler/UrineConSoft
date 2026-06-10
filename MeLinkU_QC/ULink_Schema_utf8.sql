USE [ULink]
GO
/****** Object:  Table [dbo].[AutoPcSet]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[AutoPcSet](
	[DOC] [varchar](50) NOT NULL,
	[PCId] [varchar](50) NULL,
	[PCNetID] [varchar](50) NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[AutoUser]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AutoUser](
	[Login_Type] [nvarchar](50) NULL,
	[UserID] [nvarchar](50) NULL,
	[LoginTime] [datetime] NULL
) ON [PRIMARY]

GO
/****** Object:  Table [dbo].[AutoUser_Record]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[AutoUser_Record](
	[Login_Type] [nvarchar](50) NULL,
	[UserID] [nvarchar](50) NULL,
	[LoginTime] [datetime] NULL,
	[Inote] [nvarchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
/****** Object:  Table [dbo].[AVrule]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[AVrule](
	[ser] [bigint] IDENTITY(1,1) NOT NULL,
	[AV_rule] [varchar](200) NOT NULL,
	[type] [varchar](50) NOT NULL,
	[process] [varchar](100) NULL,
	[cause] [varchar](100) NULL,
	[inote] [varchar](200) NULL,
	[AV_Group] [varchar](50) NULL,
	[_Send] [smallint] NULL CONSTRAINT [DF_AVrule_Send]  DEFAULT ((0)),
 CONSTRAINT [PK_Table_1] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[BackPrice]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[BackPrice](
	[item] [varchar](5) NOT NULL,
	[negative] [varchar](10) NOT NULL,
	[marker] [varchar](10) NOT NULL,
	[postive1] [varchar](10) NOT NULL,
	[postive2] [varchar](10) NOT NULL,
	[postive3] [varchar](10) NOT NULL,
	[postive4] [varchar](10) NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[CH_List]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[CH_List](
	[Item_allname] [varchar](20) NOT NULL,
	[Item_name] [varchar](10) NOT NULL,
	[Item_Value] [varchar](10) NOT NULL,
	[Item_Price] [varchar](10) NULL,
	[Item_flag] [varchar](10) NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[CtrTest]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[CtrTest](
	[ser] [int] IDENTITY(1,1) NOT NULL,
	[mhId] [char](4) NOT NULL,
	[cId] [char](4) NOT NULL,
	[mtId] [varchar](10) NOT NULL,
	[hLtId] [bigint] NULL,
	[tea] [varchar](10) NOT NULL CONSTRAINT [DF__CtrTest__tea__1ED998B2]  DEFAULT ((0)),
	[cva] [real] NOT NULL CONSTRAINT [DF__CtrTest__cva__1FCDBCEB]  DEFAULT ((0)),
	[TA] [real] NOT NULL CONSTRAINT [DF__CtrTest__TA__20C1E124]  DEFAULT ((0)),
	[SDI] [real] NOT NULL CONSTRAINT [DF__CtrTest__SDI__21B6055D]  DEFAULT ((0)),
	[SIGMA] [real] NOT NULL CONSTRAINT [DF__CtrTest__SIGMA__22AA2996]  DEFAULT ((0)),
	[BIAS] [real] NOT NULL CONSTRAINT [DF__CtrTest__BIAS__239E4DCF]  DEFAULT ((0)),
 CONSTRAINT [PK_CtrTest] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[DailyQC]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[DailyQC](
	[dqcId] [bigint] IDENTITY(1,1) NOT NULL,
	[mhId] [char](4) NOT NULL,
	[cId] [char](4) NOT NULL,
	[mtId] [varchar](10) NOT NULL,
	[iValue] [real] NULL,
	[iDate] [datetime] NOT NULL,
	[iUser] [varchar](20) NULL,
	[lot] [varchar](40) NULL CONSTRAINT [DF_DailyQC_lot]  DEFAULT (''),
	[ltId] [bigint] NULL CONSTRAINT [DF_DailyQC_ltId]  DEFAULT ((0)),
	[sdFlag] [smallint] NULL CONSTRAINT [DF__DailyQC__sdFlag__403A8C7D]  DEFAULT ((0)),
	[iFlag1] [tinyint] NOT NULL CONSTRAINT [DF_DailyQC_iFlag1]  DEFAULT ((0)),
	[iFlag2] [tinyint] NOT NULL CONSTRAINT [DF_DailyQC_iFlag2]  DEFAULT ((1)),
	[iFlag3] [tinyint] NOT NULL CONSTRAINT [DF_DailyQC_iFlag3]  DEFAULT ((0)),
	[iFlag4] [smallint] NOT NULL CONSTRAINT [DF_DailyQC_iFlag4]  DEFAULT ((-1)),
	[iFlag5] [tinyint] NOT NULL CONSTRAINT [DF__DailyQC__iFlag5__44FF419A]  DEFAULT ((0)),
	[vDate] [datetime] NULL,
	[sysTime] [datetime] NOT NULL CONSTRAINT [DF__DailyQC__sysTime__45F365D3]  DEFAULT (getdate()),
	[Check_Type] [char](1) NULL CONSTRAINT [DF_DailyQC_Check_Type]  DEFAULT ('0'),
 CONSTRAINT [PK_DailyQC] PRIMARY KEY CLUSTERED 
(
	[dqcId] ASC,
	[mhId] ASC,
	[mtId] ASC,
	[iDate] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[DpmDetails]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[DpmDetails](
	[ser] [int] IDENTITY(1,1) NOT NULL,
	[dpmId] [int] NOT NULL CONSTRAINT [DF__DpmDetail__dpmID__4AB81AF0]  DEFAULT ((0)),
	[mhId] [char](4) NOT NULL CONSTRAINT [DF__DpmDetails__mhID__4BAC3F29]  DEFAULT (''),
 CONSTRAINT [PK_DpmDetails] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[DpmMaster]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[DpmMaster](
	[depId] [int] IDENTITY(1,1) NOT NULL,
	[depName] [varchar](40) NOT NULL DEFAULT (''),
 CONSTRAINT [PK_DpmMaster] PRIMARY KEY CLUSTERED 
(
	[depId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[ErrNotes]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[ErrNotes](
	[ErId] [bigint] IDENTITY(1,1) NOT NULL,
	[dqcId] [bigint] NOT NULL,
	[detail1] [text] NULL,
	[iUser] [varchar](20) NULL,
	[iDate] [datetime] NULL,
	[detail2] [text] NULL DEFAULT (''),
	[detail3] [text] NULL DEFAULT ('')
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[Explain]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[Explain](
	[ser] [bigint] IDENTITY(1,1) NOT NULL,
	[iType] [varchar](10) NULL,
	[icode] [nvarchar](10) NULL,
	[iText] [nvarchar](200) NULL,
 CONSTRAINT [PK_Explain] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[Lot_Overlapping]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[Lot_Overlapping](
	[New_Lot_ID] [varchar](50) NOT NULL,
	[Old_Lot_ID] [varchar](50) NOT NULL,
	[New_Lot_ID_Value] [varchar](50) NOT NULL,
	[Old_ltId] [varchar](10) NOT NULL,
	[Lot_Level] [varchar](10) NOT NULL,
	[writeDate] [datetime] NOT NULL,
	[od] [varchar](50) NOT NULL,
	[mhId] [varchar](10) NOT NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[LotTable]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[LotTable](
	[od] [varchar](10) NOT NULL,
	[mhId] [varchar](10) NOT NULL,
	[lot] [varchar](40) NOT NULL,
	[lot_id] [varchar](40) NOT NULL,
	[lot_Level] [varchar](20) NOT NULL,
	[QC_date] [datetime] NOT NULL,
	[Writedate] [datetime] NOT NULL,
	[iUser] [varchar](40) NOT NULL,
	[lot_type] [varchar](10) NOT NULL,
	[cName] [varchar](10) NULL CONSTRAINT [DF_LotTable_cName]  DEFAULT ('')
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[LotTest]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[LotTest](
	[ltId] [bigint] IDENTITY(1,1) NOT NULL,
	[mhId] [char](4) NOT NULL,
	[cId] [char](4) NOT NULL,
	[mtId] [varchar](10) NOT NULL,
	[lot] [varchar](40) NOT NULL,
	[tMean] [real] NOT NULL CONSTRAINT [DF_lotTest_tMean]  DEFAULT ((0)),
	[tSd] [real] NOT NULL CONSTRAINT [DF_lotTest_tSd]  DEFAULT ((0)),
	[Range] [varchar](20) NULL,
	[CVA] [real] NULL CONSTRAINT [DF_LotTest_CVA]  DEFAULT ('0'),
	[TEA] [varchar](10) NULL CONSTRAINT [DF_LotTest_TEA]  DEFAULT ('0'),
	[iDateTime] [datetime] NULL,
	[iUser] [varchar](20) NULL,
	[LotStyle] [char](1) NULL CONSTRAINT [DF__LotTest__LotStyl__1AD3FDA4]  DEFAULT ('Y'),
	[TA] [varchar](20) NULL CONSTRAINT [DF_LotTest_TA]  DEFAULT ('0'),
	[SDI] [varchar](20) NULL CONSTRAINT [DF_LotTest_SDI]  DEFAULT ('0'),
	[SIGMA] [varchar](20) NULL CONSTRAINT [DF_LotTest_SIGMA]  DEFAULT ('0'),
	[BIAS] [varchar](20) NULL CONSTRAINT [DF_LotTest_BIAS]  DEFAULT ('0'),
 CONSTRAINT [PK_LotTest] PRIMARY KEY CLUSTERED 
(
	[ltId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[melinkLimit]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[melinkLimit](
	[verId] [char](4) NOT NULL,
	[sysCode] [char](1) NOT NULL,
	[modCode] [char](3) NOT NULL,
	[modName] [varchar](20) NOT NULL,
	[modNote] [varchar](200) NOT NULL,
 CONSTRAINT [PK_melinkLimit] PRIMARY KEY CLUSTERED 
(
	[verId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[menber]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[menber](
	[menberId] [varchar](50) NOT NULL,
	[menberPw] [varchar](50) NOT NULL,
	[menberName] [varchar](50) NOT NULL,
	[companyId] [varchar](50) NULL,
	[iopen] [varchar](50) NOT NULL,
	[od] [varchar](50) NULL,
	[DepartmentID] [varchar](50) NULL,
 CONSTRAINT [PK_menber] PRIMARY KEY CLUSTERED 
(
	[menberId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[menberLimit]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[menberLimit](
	[menberId] [varchar](10) NOT NULL CONSTRAINT [DF_menberLinit_menberId]  DEFAULT (''),
	[sysCode] [char](1) NOT NULL,
	[modCode] [char](3) NOT NULL,
 CONSTRAINT [PK_menberLinit] PRIMARY KEY CLUSTERED 
(
	[menberId] ASC,
	[sysCode] ASC,
	[modCode] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[menberLoginRecord]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[menberLoginRecord](
	[clientName] [varchar](max) NOT NULL,
	[menberID] [varchar](50) NOT NULL,
	[menberName] [varchar](50) NOT NULL,
	[loginTime] [datetime] NULL CONSTRAINT [DF_menberLoginRecord_loginTime]  DEFAULT (getdate())
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[MhCampus]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[MhCampus](
	[od] [varchar](10) NOT NULL,
	[CampusName] [varchar](50) NOT NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[MhCtrMaster]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[MhCtrMaster](
	[ser] [int] IDENTITY(1,1) NOT NULL,
	[mhId] [char](4) NOT NULL,
	[cId] [char](4) NOT NULL,
	[cName] [varchar](40) NULL,
	[bpId] [char](12) NOT NULL,
	[hLot] [varchar](40) NULL,
	[cLevel] [tinyint] NOT NULL,
 CONSTRAINT [PK_MhCtrMaster] PRIMARY KEY CLUSTERED 
(
	[ser] ASC,
	[mhId] ASC,
	[cId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[MhDepartment]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[MhDepartment](
	[DepartmentID] [varchar](10) NOT NULL,
	[DepartmentName] [varchar](50) NOT NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[MhItem]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[MhItem](
	[mhcode] [varchar](50) NOT NULL,
	[mtId] [varchar](10) NOT NULL,
	[mhitem] [varchar](50) NOT NULL,
	[itemtype] [varchar](10) NOT NULL,
 CONSTRAINT [PK_MhItem] PRIMARY KEY CLUSTERED 
(
	[mhcode] ASC,
	[mtId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[MhMaster]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[MhMaster](
	[mhId] [varchar](50) NOT NULL,
	[mhName] [varchar](50) NOT NULL,
	[od] [varchar](50) NULL,
	[mhcode] [varchar](50) NULL,
	[DepartmentID] [varchar](50) NULL,
 CONSTRAINT [PK_MhMaster] PRIMARY KEY CLUSTERED 
(
	[mhId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[MhTable]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[MhTable](
	[mhcode] [varchar](50) NOT NULL,
	[mhName] [varchar](50) NOT NULL,
 CONSTRAINT [PK_MhTable] PRIMARY KEY CLUSTERED 
(
	[mhcode] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[MhTest]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[MhTest](
	[ser] [bigint] IDENTITY(1,1) NOT NULL,
	[mhId] [varchar](50) NOT NULL,
	[mtId] [varchar](50) NULL,
	[mtName] [varchar](50) NOT NULL,
	[mDp] [real] NULL,
	[wmr] [real] NULL,
	[TeaFlag] [real] NULL,
	[iUnit] [varchar](50) NULL,
	[iFlag1] [real] NULL,
	[iDaily] [tinyint] NULL,
	[itemtype] [varchar](10) NULL,
	[itemRule] [varchar](10) NULL,
 CONSTRAINT [PK_MhTest] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[Operator]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
CREATE TABLE [dbo].[Operator](
	[Oper_ID] [nvarchar](10) NULL,
	[Oper_Passwd] [nvarchar](12) NULL,
	[Oper_Name] [nvarchar](20) NULL,
	[Oper_Type] [nvarchar](1) NULL,
	[Oper_Authority] [nvarchar](100) NULL
) ON [PRIMARY]

GO
/****** Object:  Table [dbo].[Parameter]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[Parameter](
	[ID] [varchar](40) NOT NULL,
	[iValue] [text] NOT NULL,
 CONSTRAINT [PK_Parameter] PRIMARY KEY CLUSTERED 
(
	[ID] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[PCSet]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[PCSet](
	[PCId] [varchar](50) NOT NULL,
	[MhId] [varchar](10) NOT NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[Phrase]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[Phrase](
	[preId] [bigint] IDENTITY(1,1) NOT NULL,
	[wId] [varchar](20) NOT NULL CONSTRAINT [DF_Phrase_wId]  DEFAULT (''),
	[flag1] [tinyint] NOT NULL CONSTRAINT [DF_Phrase_flag1]  DEFAULT ((1)),
	[flag2] [tinyint] NOT NULL CONSTRAINT [DF_Phrase_flag2]  DEFAULT ((1)),
	[txt] [text] NOT NULL CONSTRAINT [DF_Phrase_txt]  DEFAULT (''),
 CONSTRAINT [PK_Phrase] PRIMARY KEY CLUSTERED 
(
	[preId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[PResult]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[PResult](
	[PatientKey] [bigint] IDENTITY(1,1) NOT NULL,
	[PatientName] [varchar](30) NOT NULL,
	[PatientID] [varchar](20) NULL,
	[ID_Card] [varchar](15) NULL,
	[BirthDay] [varchar](20) NOT NULL,
	[P_AGE] [varchar](5) NULL,
	[P_SEX] [varchar](10) NULL,
	[barcode] [varchar](20) NULL,
 CONSTRAINT [PK_PResult] PRIMARY KEY CLUSTERED 
(
	[PatientKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCaberrant]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCaberrant](
	[aberrantNO] [varchar](20) NOT NULL,
	[dqcId] [bigint] NOT NULL,
	[UserName] [varchar](50) NOT NULL,
	[mhName] [varchar](50) NOT NULL,
	[WriteDate] [datetime] NOT NULL,
	[IncidentTime] [datetime] NOT NULL,
	[MhId] [varchar](max) NOT NULL,
	[lot] [varchar](max) NOT NULL,
	[Err_Lab] [varchar](50) NULL,
	[RepeatChk] [char](2) NOT NULL,
	[Repeatcycle] [varchar](50) NULL,
	[Cause] [varchar](max) NOT NULL,
	[UserFunction] [varchar](max) NOT NULL,
	[FunctionResult] [varchar](max) NULL,
	[Precaution] [varchar](max) NULL,
	[ClassSign1] [varchar](50) NULL,
	[inote1] [varchar](max) NULL,
	[ClassSign2] [varchar](50) NULL,
	[inote2] [varchar](max) NULL,
	[ClassSign3] [varchar](50) NULL,
	[inote3] [varchar](max) NULL,
 CONSTRAINT [PK_QCaberrant] PRIMARY KEY CLUSTERED 
(
	[aberrantNO] ASC,
	[dqcId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCCheck]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCCheck](
	[dqcId] [bigint] NOT NULL,
	[mhId] [char](4) NOT NULL,
	[cId] [char](4) NOT NULL,
	[mtId] [varchar](10) NOT NULL,
	[iDate] [datetime] NOT NULL,
	[UserName] [varchar](50) NOT NULL,
	[UserFunction] [varchar](max) NULL,
 CONSTRAINT [PK_QCCheck] PRIMARY KEY CLUSTERED 
(
	[dqcId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCCode]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCCode](
	[Barcode] [varchar](50) NOT NULL,
	[lot] [varchar](50) NOT NULL,
	[mhId] [varchar](50) NOT NULL,
	[cId] [varchar](50) NOT NULL,
	[writeDate] [datetime] NOT NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCdraftnote]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCdraftnote](
	[ser] [bigint] IDENTITY(1,1) NOT NULL,
	[inote] [varchar](max) NOT NULL,
	[drafttype] [varchar](50) NOT NULL,
 CONSTRAINT [PK_QCdraftnote] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCFromData]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCFromData](
	[dataKey] [varchar](max) NOT NULL,
	[MhId] [varchar](50) NOT NULL,
	[MtId] [varchar](50) NOT NULL,
	[cause] [varchar](max) NOT NULL,
	[inote] [varchar](max) NOT NULL,
	[AfterValue] [char](10) NOT NULL,
	[inormal] [varchar](20) NOT NULL,
	[iNo] [char](10) NOT NULL,
	[SID] [varchar](20) NOT NULL,
	[OldValue] [varchar](50) NOT NULL,
	[NewValue] [varchar](50) NOT NULL,
	[diff] [varchar](50) NOT NULL,
	[ans] [varchar](50) NOT NULL,
	[TestValue] [varchar](50) NOT NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCFromRecord]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCFromRecord](
	[QCFromKey] [varchar](max) NOT NULL,
	[UserName] [varchar](50) NOT NULL,
	[WriteDate] [datetime] NOT NULL,
	[iType] [varchar](10) NOT NULL,
	[inote] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCFromTable]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCFromTable](
	[QCFromKey] [varchar](max) NOT NULL,
	[dqcId] [bigint] NULL,
	[FromType] [varchar](50) NOT NULL,
	[UserName] [varchar](50) NOT NULL,
	[mhName] [varchar](50) NOT NULL,
	[WriteDate] [datetime] NOT NULL,
	[iType] [char](10) NOT NULL,
	[ClassSign1] [varchar](50) NULL,
	[inote1] [varchar](max) NULL,
	[iTime1] [datetime] NULL,
	[ClassSign2] [varchar](50) NULL,
	[inote2] [varchar](max) NULL,
	[iTime2] [datetime] NULL,
	[ClassSign3] [varchar](50) NULL,
	[inote3] [varchar](max) NULL,
	[iTime3] [datetime] NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCpass]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCpass](
	[MachineId] [varchar](10) NOT NULL,
	[item] [varchar](10) NOT NULL,
	[pass] [varchar](1) NOT NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCRecordEven]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCRecordEven](
	[ser] [bigint] IDENTITY(1,1) NOT NULL,
	[iDate] [datetime] NOT NULL,
	[iUser] [varchar](50) NOT NULL,
	[iClass] [varchar](20) NOT NULL,
	[iTex] [text] NULL,
 CONSTRAINT [PK_QC] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QcSignRecord]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QcSignRecord](
	[dqcId] [bigint] NOT NULL,
	[signType] [char](1) NOT NULL CONSTRAINT [DF_QcSignRecord_signType]  DEFAULT ('A'),
	[writeTime] [datetime] NOT NULL CONSTRAINT [DF_QcSignRecord_writeTime]  DEFAULT (getdate()),
	[signId] [varchar](20) NOT NULL CONSTRAINT [DF_QcSignRecord_signId]  DEFAULT (''),
	[signName] [varchar](40) NOT NULL CONSTRAINT [DF_QcSignRecord_signName]  DEFAULT (''),
	[iflag1] [char](1) NOT NULL CONSTRAINT [DF_QcSignRecord_iflag1]  DEFAULT ('T'),
	[iflag2] [char](1) NOT NULL CONSTRAINT [DF_QcSignRecord_iflag2]  DEFAULT ('D'),
	[iflag3] [char](1) NULL CONSTRAINT [DF_QcSignRecord_iflag3]  DEFAULT (''),
	[iflag4] [char](1) NULL CONSTRAINT [DF_QcSignRecord_iflag4]  DEFAULT (''),
	[iNote] [varchar](50) NOT NULL CONSTRAINT [DF_QcSignRecord_iNote]  DEFAULT (''),
 CONSTRAINT [PK_QcSignRecord] PRIMARY KEY CLUSTERED 
(
	[dqcId] ASC,
	[signType] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCStatDaily]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCStatDaily](
	[ser] [bigint] IDENTITY(1,1) NOT NULL,
	[QsId] [bigint] NOT NULL CONSTRAINT [DF__QCStatDail__QsId__31583BA0]  DEFAULT ((0)),
	[mhId] [char](4) NOT NULL CONSTRAINT [DF__QCStatDail__mhId__324C5FD9]  DEFAULT (''),
	[cId] [char](4) NOT NULL CONSTRAINT [DF__QCStatDaily__cId__33408412]  DEFAULT (''),
	[mtId] [varchar](10) NOT NULL CONSTRAINT [DF__QCStatDail__mtId__3434A84B]  DEFAULT (''),
	[iValue] [real] NOT NULL CONSTRAINT [DF__QCStatDai__iValu__3528CC84]  DEFAULT ((0)),
	[iDate] [datetime] NULL,
	[vDate] [datetime] NULL,
	[iUser] [varchar](20) NULL CONSTRAINT [DF__QCStatDai__iUser__361CF0BD]  DEFAULT (''),
	[lot] [varchar](40) NOT NULL CONSTRAINT [DF__QCStatDaily__lot__371114F6]  DEFAULT (''),
	[ltId] [bigint] NOT NULL CONSTRAINT [DF__QCStatDail__ltId__3805392F]  DEFAULT ((0)),
	[sdFlag] [smallint] NOT NULL CONSTRAINT [DF__QCStatDai__sdFla__38F95D68]  DEFAULT ((0)),
	[iFlag4] [smallint] NOT NULL CONSTRAINT [DF__QCStatDai__iFlag__39ED81A1]  DEFAULT ((-1)),
	[iText1] [text] NULL CONSTRAINT [DF__QCStatDai__iText__3AE1A5DA]  DEFAULT (''),
	[iText2] [text] NULL CONSTRAINT [DF__QCStatDai__iText__3BD5CA13]  DEFAULT (''),
	[eUser] [varchar](20) NULL CONSTRAINT [DF__QCStatDai__eUser__3CC9EE4C]  DEFAULT (''),
	[eDate] [datetime] NULL,
 CONSTRAINT [PK_QCStatDaily] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCStatDetail]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCStatDetail](
	[ser] [bigint] IDENTITY(1,1) NOT NULL,
	[QsId] [bigint] NOT NULL CONSTRAINT [DF__QCStatDeta__QsId__18EBB532]  DEFAULT ((0)),
	[pageN] [int] NOT NULL CONSTRAINT [DF__QCStatDet__pageN__19DFD96B]  DEFAULT ((0)),
	[cId] [char](4) NOT NULL CONSTRAINT [DF__QCStatDetai__cId__1AD3FDA4]  DEFAULT (''),
	[cName] [varchar](40) NOT NULL CONSTRAINT [DF__QCStatDet__cName__1BC821DD]  DEFAULT (''),
	[lot] [varchar](40) NOT NULL CONSTRAINT [DF__QCStatDetai__lot__1CBC4616]  DEFAULT (''),
	[ltId] [bigint] NOT NULL CONSTRAINT [DF__QCStatDeta__ltId__1DB06A4F]  DEFAULT ((0)),
	[ilevel] [tinyint] NOT NULL CONSTRAINT [DF__QCStatDet__ileve__1EA48E88]  DEFAULT ((0)),
	[iUnit] [varchar](10) NOT NULL CONSTRAINT [DF__QCStatDet__iUnit__1F98B2C1]  DEFAULT (''),
	[iSymbol] [char](1) NOT NULL CONSTRAINT [DF__QCStatDet__iSymb__208CD6FA]  DEFAULT (''),
	[tMean] [real] NOT NULL CONSTRAINT [DF__QCStatDet__tMean__2180FB33]  DEFAULT ((0)),
	[tSd] [real] NOT NULL CONSTRAINT [DF__QCStatDetai__tSd__22751F6C]  DEFAULT ((0)),
	[aMean] [real] NOT NULL CONSTRAINT [DF__QCStatDet__aMean__236943A5]  DEFAULT ((0)),
	[aSd] [real] NOT NULL CONSTRAINT [DF__QCStatDetai__aSd__245D67DE]  DEFAULT ((0)),
	[aCv] [real] NOT NULL CONSTRAINT [DF__QCStatDetai__aCv__25518C17]  DEFAULT ((0)),
	[SDI] [real] NOT NULL CONSTRAINT [DF__QCStatDetai__SDI__2645B050]  DEFAULT ((0)),
	[Bias] [real] NOT NULL CONSTRAINT [DF__QCStatDeta__Bias__2739D489]  DEFAULT ((0)),
	[TE] [real] NOT NULL CONSTRAINT [DF__QCStatDetail__TE__282DF8C2]  DEFAULT ((0)),
	[Sigma] [real] NOT NULL CONSTRAINT [DF__QCStatDet__Sigma__29221CFB]  DEFAULT ((0)),
	[N] [int] NOT NULL CONSTRAINT [DF__QCStatDetail__N__2A164134]  DEFAULT ((0)),
	[FlagN] [tinyint] NOT NULL CONSTRAINT [DF__QCStatDet__FlagN__2B0A656D]  DEFAULT ((0)),
	[stdTea] [real] NOT NULL CONSTRAINT [DF__QCStatDet__stdTe__2BFE89A6]  DEFAULT ((0)),
	[FlagTea] [tinyint] NOT NULL CONSTRAINT [DF__QCStatDet__FlagT__2CF2ADDF]  DEFAULT ((0)),
	[stdCva] [real] NOT NULL CONSTRAINT [DF__QCStatDet__stdCv__2DE6D218]  DEFAULT ((0)),
	[FlagCva] [tinyint] NOT NULL CONSTRAINT [DF__QCStatDet__FlagC__2EDAF651]  DEFAULT ((0)),
	[stdSDR] [real] NOT NULL CONSTRAINT [DF__QCStatDet__stdSD__2FCF1A8A]  DEFAULT ((0)),
	[FlagSDR] [tinyint] NOT NULL CONSTRAINT [DF__QCStatDet__FlagS__30C33EC3]  DEFAULT ((0)),
	[stdSDI] [real] NOT NULL CONSTRAINT [DF__QCStatDet__stdSD__31B762FC]  DEFAULT ((0)),
	[FlagSDI] [tinyint] NOT NULL CONSTRAINT [DF__QCStatDet__FlagS__32AB8735]  DEFAULT ((0)),
	[stdSigma] [real] NOT NULL CONSTRAINT [DF__QCStatDet__stdSi__339FAB6E]  DEFAULT ((0)),
	[FlagSigma] [tinyint] NOT NULL CONSTRAINT [DF__QCStatDet__FlagS__3493CFA7]  DEFAULT ((0)),
	[stdBias] [real] NOT NULL CONSTRAINT [DF__QCStatDet__stdBi__3587F3E0]  DEFAULT ((0)),
	[FlagBias] [tinyint] NOT NULL CONSTRAINT [DF__QCStatDet__FlagB__367C1819]  DEFAULT ((0)),
	[iUser] [varchar](20) NULL CONSTRAINT [DF__QCStatDet__iUser__37703C52]  DEFAULT (''),
	[iDateTime] [datetime] NULL,
	[iTex] [text] NULL CONSTRAINT [DF__QCStatDeta__iTex__3864608B]  DEFAULT (''),
	[iFlag1] [tinyint] NULL CONSTRAINT [DF__QCStatDet__iFlag__395884C4]  DEFAULT ((0)),
	[mtId] [varchar](10) NULL CONSTRAINT [DF__QCStatDeta__mtId__3A4CA8FD]  DEFAULT (''),
	[mtName] [varchar](40) NULL CONSTRAINT [DF__QCStatDet__mtNam__3B40CD36]  DEFAULT (''),
 CONSTRAINT [PK_QCStatDetail] PRIMARY KEY CLUSTERED 
(
	[ser] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[QCStatTitle]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[QCStatTitle](
	[QsId] [bigint] NOT NULL,
	[mhId] [char](4) NOT NULL CONSTRAINT [DF__QCStatTitl__mhId__0B91BA14]  DEFAULT (''),
	[sDate] [char](10) NOT NULL CONSTRAINT [DF__QCStatTit__sDate__0C85DE4D]  DEFAULT (''),
	[eDate] [char](10) NOT NULL CONSTRAINT [DF__QCStatTit__eDate__0D7A0286]  DEFAULT (''),
	[iDateTime] [datetime] NOT NULL CONSTRAINT [DF_QCStatTitle_iDateTime]  DEFAULT (getdate()),
	[iUser] [varchar](20) NULL CONSTRAINT [DF__QCStatTit__iUser__0E6E26BF]  DEFAULT (''),
	[aCount] [int] NOT NULL CONSTRAINT [DF__QCStatTit__aCoun__0F624AF8]  DEFAULT ((0)),
	[cCount] [int] NOT NULL CONSTRAINT [DF__QCStatTit__cCoun__10566F31]  DEFAULT ((0)),
	[iFlag1] [tinyint] NOT NULL CONSTRAINT [DF__QCStatTit__iFlag__114A936A]  DEFAULT ((0)),
 CONSTRAINT [PK_QCStatTitle_1] PRIMARY KEY CLUSTERED 
(
	[QsId] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[ReagentData]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[ReagentData](
	[dataKey] [varchar](max) NOT NULL,
	[datatime] [datetime] NOT NULL,
	[Value1] [varchar](max) NOT NULL,
	[QCValue] [varchar](max) NULL,
	[ItemValue] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[RerunOrder]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[RerunOrder](
	[Barcode] [varchar](50) NOT NULL,
	[OrderValue] [varchar](10) NOT NULL,
	[ReSend] [varchar](1) NULL CONSTRAINT [DF_RerunOrder_ReSend]  DEFAULT ('N'),
 CONSTRAINT [PK_RerunOrder] PRIMARY KEY CLUSTERED 
(
	[Barcode] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[ReSultNote]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[ReSultNote](
	[ser] [bigint] IDENTITY(1,1) NOT NULL,
	[resultnote] [varchar](max) NOT NULL,
	[MhId] [varchar](50) NOT NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[ResultTable]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[ResultTable](
	[ResultKey] [bigint] IDENTITY(1,1) NOT NULL,
	[PatientKey] [bigint] NULL,
	[machineId] [varchar](50) NOT NULL,
	[barcode] [varchar](50) NOT NULL,
	[writeDate] [datetime] NOT NULL,
	[Itype] [varchar](10) NOT NULL,
	[D_Name] [varchar](50) NULL,
	[D_result] [varchar](50) NULL,
	[F_Result] [varchar](50) NULL,
	[Comment] [varchar](max) NULL,
	[CheckTime] [datetime] NULL,
	[CheckName] [varchar](50) NULL,
	[CheckID] [varchar](50) NULL,
	[inote] [varchar](max) NULL,
	[Sno] [nchar](10) NOT NULL,
	[ChartNo] [nchar](10) NOT NULL,
	[AcptDate] [varchar](50) NULL,
	[AcptTime] [varchar](50) NULL,
	[Emergency] [nchar](1) NULL,
	[Validated] [nchar](1) NULL,
	[Rwrite] [varchar](1) NULL CONSTRAINT [DF_ResultTable_Rwrite]  DEFAULT ('F'),
	[UserName] [varchar](20) NULL,
	[MachValidated] [varchar](30) NULL,
 CONSTRAINT [PK_ResultTable] PRIMARY KEY CLUSTERED 
(
	[ResultKey] ASC
)WITH (PAD_INDEX = OFF, STATISTICS_NORECOMPUTE = OFF, IGNORE_DUP_KEY = OFF, ALLOW_ROW_LOCKS = ON, ALLOW_PAGE_LOCKS = ON) ON [PRIMARY]
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[ResultTable_NO]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[ResultTable_NO](
	[ResultKey] [bigint] NOT NULL,
	[writeDate] [datetime] NOT NULL,
	[Itype] [varchar](50) NULL,
	[CheckName] [varchar](50) NULL,
	[CheckID] [varchar](50) NULL,
	[inote] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[S_List]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[S_List](
	[Item_allname] [varchar](50) NOT NULL,
	[Item_neme] [varchar](20) NOT NULL,
	[Item_value] [varchar](20) NOT NULL,
	[Item_group] [varchar](10) NOT NULL,
	[Item_nurmal] [varchar](10) NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[SavePath]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[SavePath](
	[Path] [varchar](100) NOT NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[SP_Note]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[SP_Note](
	[ser] [int] IDENTITY(1,1) NOT NULL,
	[writeDate] [datetime] NOT NULL,
	[PatientID] [varchar](50) NOT NULL,
	[INote] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[Sprice]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[Sprice](
	[S_item] [varchar](50) NOT NULL,
	[Value1] [real] NOT NULL,
	[Value2] [real] NULL,
	[Value3] [real] NULL,
	[Value4] [real] NULL,
	[Value5] [real] NULL,
	[Value6] [real] NULL,
	[Value7] [real] NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[TOrder]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[TOrder](
	[Instrument] [varchar](10) NOT NULL,
	[ID] [varchar](20) NOT NULL,
	[Item] [varchar](50) NULL,
	[PatientId] [varchar](10) NULL,
	[writeDate] [datetime] NOT NULL CONSTRAINT [DF_TOrder_writeDate]  DEFAULT (getdate()),
	[Transfer] [nchar](2) NOT NULL CONSTRAINT [DF_TOrder_Transfer]  DEFAULT ('F'),
	[Sno] [nchar](10) NULL,
	[ChartNo] [nchar](10) NULL,
	[SendMachineId] [varchar](50) NULL,
	[AcptDate] [varchar](10) NULL,
	[AcptTime] [varchar](10) NULL,
	[Dname] [varchar](10) NULL,
	[Fname] [varchar](10) NULL,
	[Emergency] [nchar](1) NULL,
	[I001] [nchar](1) NULL CONSTRAINT [DF_TOrder_I001]  DEFAULT ('F'),
	[I002] [nchar](1) NULL CONSTRAINT [DF_TOrder_I002]  DEFAULT ('F'),
	[I003] [nchar](1) NULL CONSTRAINT [DF_TOrder_I003]  DEFAULT ('F')
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[TOrder_ec]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[TOrder_ec](
	[Instrument] [varchar](50) NOT NULL,
	[ID] [varchar](50) NOT NULL,
	[Item] [varchar](50) NULL,
	[PatientId] [varchar](50) NULL,
	[writeDate] [datetime] NOT NULL,
	[Transfer] [nchar](2) NOT NULL,
	[Sno] [nchar](10) NULL,
	[ChartNo] [nchar](10) NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[TResult]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[TResult](
	[ResultKey] [bigint] NOT NULL,
	[Instrument] [varchar](50) NOT NULL,
	[ID] [varchar](50) NOT NULL,
	[Item] [varchar](50) NOT NULL,
	[Barcode] [varchar](50) NOT NULL,
	[type] [varchar](50) NOT NULL,
	[Fstatus] [int] NOT NULL,
	[Price] [varchar](50) NOT NULL,
	[new_Result] [varchar](50) NULL,
	[Result] [varchar](50) NOT NULL,
	[Flag] [varchar](50) NOT NULL,
	[Flag_Mod] [varchar](50) NOT NULL,
	[iclass] [varchar](50) NULL,
	[T1] [datetime] NULL,
	[T2] [datetime] NULL,
	[T3] [datetime] NULL,
	[T4] [datetime] NULL,
	[T5] [datetime] NULL,
	[iNote] [varchar](max) NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[TResult_NO]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[TResult_NO](
	[ResultKey] [varchar](50) NOT NULL,
	[writeDate] [datetime] NOT NULL,
	[Item] [varchar](50) NOT NULL,
	[Barcode] [varchar](50) NULL,
	[new_Result] [varchar](50) NULL,
	[T1] [datetime] NULL,
	[T2] [datetime] NULL,
	[T3] [datetime] NULL,
	[T4] [datetime] NULL,
	[T5] [datetime] NULL,
	[iNote] [varchar](max) NULL,
	[ChangeName] [varchar](50) NULL,
	[ChangeID] [varchar](50) NOT NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[TT_DIC]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[TT_DIC](
	[dic_code] [varchar](20) NOT NULL,
	[item_name] [varchar](50) NOT NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[TTset]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[TTset](
	[SetName] [varchar](50) NOT NULL,
	[SetValue] [varchar](50) NOT NULL,
	[SETMACH] [varchar](50) NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[TTSset]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[TTSset](
	[TTname] [varchar](50) NOT NULL,
	[TTflag] [varchar](20) NOT NULL,
	[TTshow] [varchar](10) NOT NULL CONSTRAINT [DF_TTset_TTshow]  DEFAULT ('T'),
	[TTALLName] [varchar](50) NULL,
	[TTGroup] [varchar](10) NULL
) ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
/****** Object:  Table [dbo].[ULink_LOG]    Script Date: 2026/6/10 上午 09:12:28 ******/
SET ANSI_NULLS ON
GO
SET QUOTED_IDENTIFIER ON
GO
SET ANSI_PADDING ON
GO
CREATE TABLE [dbo].[ULink_LOG](
	[LOG_NAME] [varchar](50) NOT NULL,
	[LOG_TIME] [datetime] NOT NULL,
	[LOG_VALUE] [varchar](max) NOT NULL
) ON [PRIMARY] TEXTIMAGE_ON [PRIMARY]

GO
SET ANSI_PADDING OFF
GO
ALTER TABLE [dbo].[Explain] ADD  CONSTRAINT [DF_Explain_iType]  DEFAULT ('') FOR [iType]
GO
ALTER TABLE [dbo].[Explain] ADD  CONSTRAINT [DF_Explain_icode]  DEFAULT ('') FOR [icode]
GO
ALTER TABLE [dbo].[Explain] ADD  CONSTRAINT [DF_Explain_iText]  DEFAULT ('') FOR [iText]
GO
ALTER TABLE [dbo].[Parameter] ADD  CONSTRAINT [DF_Parameter_iValue]  DEFAULT ('') FOR [iValue]
GO
ALTER TABLE [dbo].[QCRecordEven] ADD  CONSTRAINT [DF_QC_iDate]  DEFAULT (getdate()) FOR [iDate]
GO
ALTER TABLE [dbo].[QCRecordEven] ADD  CONSTRAINT [DF_QC_iUser]  DEFAULT ((20)) FOR [iUser]
GO
ALTER TABLE [dbo].[QCRecordEven] ADD  CONSTRAINT [DF_QC_iClass]  DEFAULT ('') FOR [iClass]
GO
ALTER TABLE [dbo].[QCRecordEven] ADD  CONSTRAINT [DF_Table_1_iTex1]  DEFAULT ('') FOR [iTex]
GO
ALTER TABLE [dbo].[TOrder_ec] ADD  CONSTRAINT [DF_TOrder_ec_writeDate]  DEFAULT (getdate()) FOR [writeDate]
GO
ALTER TABLE [dbo].[TOrder_ec] ADD  CONSTRAINT [DF_TOrder_ec_Transfer]  DEFAULT ('F') FOR [Transfer]
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'權限項目索引(自行給值)' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'melinkLimit', @level2type=N'COLUMN',@level2name=N'verId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'系統模組代號 S=系統 ;M=人事 ;R=試劑 ;Q=QC ;A=自動驗證 ;L=LIS' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'melinkLimit', @level2type=N'COLUMN',@level2name=N'sysCode'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'功能代號' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'melinkLimit', @level2type=N'COLUMN',@level2name=N'modCode'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'功能名稱' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'melinkLimit', @level2type=N'COLUMN',@level2name=N'modName'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'功能說明' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'melinkLimit', @level2type=N'COLUMN',@level2name=N'modNote'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'系統權限分類' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'melinkLimit'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'登入密碼(HashCode)，預設密碼''0000''' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menber', @level2type=N'COLUMN',@level2name=N'menberPw'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'人員姓名' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menber', @level2type=N'COLUMN',@level2name=N'menberName'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'廠商ID(所屬部門)' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menber', @level2type=N'COLUMN',@level2name=N'companyId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'登入開關 T=可登入 ;F=不可登入' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menber', @level2type=N'COLUMN',@level2name=N'iopen'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'人員基本資料' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menber'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'系統模組代號 S=系統 ;M=人事 ;R=試劑 ;Q=QC ;A=自動驗證 ;L=LIS' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menberLimit', @level2type=N'COLUMN',@level2name=N'sysCode'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'功能代號' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menberLimit', @level2type=N'COLUMN',@level2name=N'modCode'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'使用者權限設定' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menberLimit'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menberLoginRecord', @level2type=N'COLUMN',@level2name=N'clientName'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menberLoginRecord', @level2type=N'COLUMN',@level2name=N'menberID'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menberLoginRecord', @level2type=N'COLUMN',@level2name=N'menberName'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'menberLoginRecord', @level2type=N'COLUMN',@level2name=N'loginTime'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'DailyQC索引值' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'QcSignRecord', @level2type=N'COLUMN',@level2name=N'dqcId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'簽收類別 ex A=第一主管簽收,B=第二主管簽收....' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'QcSignRecord', @level2type=N'COLUMN',@level2name=N'signType'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'簽收時間(統一用資料庫時間)' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'QcSignRecord', @level2type=N'COLUMN',@level2name=N'writeTime'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'簽收人ID' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'QcSignRecord', @level2type=N'COLUMN',@level2name=N'signId'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'簽收人姓名' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'QcSignRecord', @level2type=N'COLUMN',@level2name=N'signName'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'允收註記 T=允收 F=不允收' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'QcSignRecord', @level2type=N'COLUMN',@level2name=N'iflag1'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'簽收類別 D=DailyQC簽收' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'QcSignRecord', @level2type=N'COLUMN',@level2name=N'iflag2'
GO
EXEC sys.sp_addextendedproperty @name=N'MS_Description', @value=N'簽收說明' , @level0type=N'SCHEMA',@level0name=N'dbo', @level1type=N'TABLE',@level1name=N'QcSignRecord', @level2type=N'COLUMN',@level2name=N'iNote'
GO
